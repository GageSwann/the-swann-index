"""`tsi run`: the whole live pipeline, as of now (what the nightly job runs).

    ingest (CFBD) -> rate (ratings + rankings, season sim) -> grade (finished games)
    -> publish (upcoming)

Everything is live: there is no replay of past weeks, because a snapshot published
after kickoff can never be the locked one, and back-dating `published_at` would fake
history (rule 2). If ingest fails, the later steps still run on the data already
stored and the failure is reported, so one CFBD hiccup doesn't skip a day of
predictions. The season sim is isolated the same way: if it fails, ratings, grading
and publishing still happen and the failure is reported.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from tsi.ingest.client import CfbdClient
from tsi.ingest.freshness import current_season
from tsi.model.artifact import ModelArtifact
from tsi.services.board import Board, build_board
from tsi.services.daily import DailyResult, run_daily
from tsi.services.grade import GradeResult, grade_picks
from tsi.services.live_inputs import load_live_inputs
from tsi.services.publish import PublishResult, publish_board
from tsi.services.rate import LiveRatings, compute_live_ratings
from tsi.services.rate_store import save_live_ratings
from tsi.services.season_sim import SeasonProjection, project_season
from tsi.services.sim_store import save_season_sim

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunResult:
    ingest: DailyResult | None  # None when skipped or failed
    ingest_error: str | None
    ratings: LiveRatings
    ratings_run_id: int | None  # None on a dry run
    sim: SeasonProjection | None  # stored under the rating run (sim_results); None if failed
    sim_error: str | None
    grade: GradeResult | None
    board: Board
    publish: PublishResult | None

    @property
    def ok(self) -> bool:
        return self.ingest_error is None and self.sim_error is None


def run_pipeline(
    sessions: sessionmaker[Session],
    now: datetime,
    artifact: ModelArtifact,
    client: CfbdClient | None = None,  # None: skip ingest
    week: tuple[str, int] | None = None,
    dry_run: bool = False,
) -> RunResult:
    daily, error = _ingest(client, sessions, now)
    with sessions() as session:
        live = load_live_inputs(session, current_season(now), now, artifact)
        ratings = compute_live_ratings(session, now, artifact, live)
        sim, sim_error = _guarded(
            "season sim", lambda: project_season(session, now, artifact, live=live)
        )
        board = build_board(session, now, artifact, week=week, live=live)
    if dry_run:
        return RunResult(daily, error, ratings, None, sim, sim_error, None, board, None)
    run_id = save_live_ratings(sessions, ratings, artifact)
    if sim is not None:
        _, sim_error = _guarded(
            "saving the season sim", lambda: save_season_sim(sessions, run_id, sim)
        )
    return RunResult(
        ingest=daily,
        ingest_error=error,
        ratings=ratings,
        ratings_run_id=run_id,
        sim=sim,
        sim_error=sim_error,
        grade=grade_picks(sessions, now),
        board=board,
        publish=publish_board(sessions, board.games, now, artifact),
    )


def _guarded[T](step: str, fn: Callable[[], T]) -> tuple[T | None, str | None]:
    """Run an optional step; on failure log and report it instead of stopping the job."""
    try:
        return fn(), None
    except Exception as exc:  # reported via RunResult.ok
        logger.exception("%s failed; continuing", step)
        return None, f"{type(exc).__name__}: {exc}"


def _ingest(
    client: CfbdClient | None, sessions: sessionmaker[Session], now: datetime
) -> tuple[DailyResult | None, str | None]:
    if client is None:
        return None, None
    try:
        return run_daily(client, sessions, now), None
    except Exception as exc:  # keep going on stored data; reported via RunResult.ok
        logger.exception("ingest failed; continuing with stored data")
        return None, f"{type(exc).__name__}: {exc}"
