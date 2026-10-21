"""Save live ratings: one `model_runs` row (kind='live') + `team_ratings` for both bases.

Each daily run is a new model_run; earlier runs are never modified, so the site can
show movement and history (rule 2 spirit).
"""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import CalendarWeek, ModelRun, TeamRating
from tsi.db.upsert import upsert_rows
from tsi.model.artifact import ModelArtifact
from tsi.services.backtest_store import current_git_sha
from tsi.services.rate import LiveRatings


def calendar_week(session: Session, season: int, now: datetime) -> tuple[str, int]:
    """(season_type, week) of the latest calendar week that has started; ('regular', 0) before."""
    row = session.execute(
        select(CalendarWeek.season_type, CalendarWeek.week)
        .where(CalendarWeek.season == season, CalendarWeek.start_date <= now)
        .order_by(CalendarWeek.start_date.desc())
        .limit(1)
    ).first()
    return (row[0], row[1]) if row else ("regular", 0)


def save_live_ratings(
    session_factory: sessionmaker[Session], live: LiveRatings, artifact: ModelArtifact
) -> int:
    with session_factory.begin() as session:
        season_type, week = calendar_week(session, live.season, live.as_of)
        run = ModelRun(
            kind="live",
            season=live.season,
            week=week,
            season_type=season_type,
            run_at=live.as_of,
            model_version=artifact.version,
            params={
                "artifact_version": artifact.version,
                "fitted_seasons": list(artifact.fitted_seasons),
                "season_hfa": live.rankings.ratings.hfa,
                "predictive_hfa": live.predictive_hfa,
                "resume_benchmark": live.rankings.benchmark,
            },
            git_sha=current_git_sha(),
        )
        session.add(run)
        session.flush()
        upsert_rows(session, TeamRating, _season_rows(run.id, live))
        upsert_rows(session, TeamRating, _predictive_rows(run.id, live))
        return run.id


def _season_rows(run_id: int, live: LiveRatings) -> list[dict[str, Any]]:
    return [
        {
            "run_id": run_id,
            "team_id": t.team_id,
            "basis": "season",
            "variant": "raw",
            "rating": t.rating,
            "off_rating": t.off,
            "def_rating": t.defense,
            "games_played": t.games,
            "provisional": t.provisional,
            "rank_power": t.rank_power,
            "sor": t.resume.sor,
            "sos": t.resume.sos,
            "rank_resume": t.rank_resume,
        }
        for t in live.rankings.teams
    ]


def _predictive_rows(run_id: int, live: LiveRatings) -> list[dict[str, Any]]:
    ordered = sorted(live.predictive, key=lambda t: -t.rating.rating)
    return [
        {
            "run_id": run_id,
            "team_id": t.team_id,
            "basis": "predictive",
            "variant": "raw",
            "rating": t.rating.rating,
            "off_rating": t.rating.off,
            "def_rating": t.rating.defense,
            "games_played": t.games,
            "provisional": t.provisional,
            "rank_power": i + 1,
        }
        for i, t in enumerate(ordered)
    ]
