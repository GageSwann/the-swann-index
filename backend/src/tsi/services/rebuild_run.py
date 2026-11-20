"""`tsi rebuild`: verify the replay on a real run, then rebuild every missing day (#152).

`verify_run` replays a stored nightly run at its exact time and compares every rating and
every forecast published at that moment (`repr`-exact): proof that the replay is the live
computation, on the database it will write to, before anything is written.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.orm import Session, sessionmaker

from tsi.db.queries.rebuilt import latest_rating_run_id, raw_published_at, run_ratings, run_time
from tsi.model.artifact import ModelArtifact
from tsi.services.rebuild import plan, rebuild_at, rebuild_day
from tsi.services.rebuild_store import StoredDay, save_rebuilt_day


@dataclass(frozen=True)
class VerifyResult:
    run_id: int
    run_at: datetime
    ratings: int
    rating_diffs: int
    forecasts: int  # board games that were published at the run's moment
    forecast_diffs: int

    @property
    def ok(self) -> bool:
        return self.ratings > 0 and self.rating_diffs == 0 and self.forecast_diffs == 0


@dataclass(frozen=True)
class DayResult:
    day: date
    store_run: bool
    teams: int  # FBS teams ranked that day (0 before the first game)
    final_games: int  # games whose last forecast before kickoff comes from this day
    stored: StoredDay | None  # None on a dry run


def latest_run(session: Session, season: int) -> int | None:
    """The newest real nightly rating run (not a rebuilt one)."""
    return latest_rating_run_id(session, season)


def verify_run(session: Session, run_id: int, artifact: ModelArtifact) -> VerifyResult:
    run_at = run_time(session, run_id)
    if run_at is None:
        raise ValueError(f"no model run {run_id}")
    day = rebuild_at(session, run_at, artifact, sims=0)
    stored = run_ratings(session, run_id)
    got: dict[tuple[int, str], tuple] = {}
    rankings = day.ratings.rankings
    for t in [*rankings.teams, *rankings.fcs_teams]:
        values = (t.rating, t.off, t.defense, t.rank_power, t.resume.sor, t.rank_resume)
        got[(t.team_id, "season")] = values
    for t in day.ratings.predictive:
        got[(t.team_id, "predictive")] = (t.rating.rating, t.rating.off, t.rating.defense)
    keys = set(got) | set(stored)
    rating_diffs = sum(1 for k in keys if repr(got.get(k)) != repr(stored.get(k)))
    published = raw_published_at(session, run_at)
    compared = [b for b in day.board if b.forecast.game.id in published]
    forecast_diffs = sum(
        1
        for b in compared
        if repr(
            (b.forecast.raw.home_points, b.forecast.raw.away_points, b.forecast.raw.home_win_prob)
        )
        != repr(published[b.forecast.game.id])
    )
    return VerifyResult(run_id, run_at, len(stored), rating_diffs, len(compared), forecast_diffs)


def rebuild_season(
    sessions: sessionmaker[Session],
    season: int,
    now: datetime,
    artifact: ModelArtifact,
    *,
    dry_run: bool = False,
    sims: int | None = None,
    on_day: Callable[[DayResult], None] | None = None,
) -> list[DayResult]:
    with sessions() as session:
        days = plan(session, season, now)
    results = []
    for p in days:
        with sessions() as session:
            kwargs = {} if sims is None else {"sims": sims}
            day = rebuild_day(session, p.day, artifact, **kwargs)
        stored = (
            None
            if dry_run
            else save_rebuilt_day(sessions, day, artifact, store_run=p.store_run, now=now)
        )
        result = DayResult(
            p.day, p.store_run, len(day.ratings.rankings.teams), len(day.final_forecasts()), stored
        )
        results.append(result)
        if on_day:
            on_day(result)
    return results
