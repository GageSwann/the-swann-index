"""Live model runs: which rating run a page shows, and when things were last published."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from tsi.db.models import ModelRun, Prediction, TeamRating


@dataclass(frozen=True)
class RunInfo:
    id: int
    season: int
    season_type: str
    week: int
    run_at: datetime
    model_version: str


def latest_rating_run(
    session: Session,
    season: int,
    week: int | None = None,
    season_type: str | None = None,
    before: datetime | None = None,
) -> RunInfo | None:
    """The newest live run with stored team ratings (daily `tsi rate`).

    Optionally within a week, or strictly before a time (the previous day's run).
    """
    query = (
        select(
            ModelRun.id,
            ModelRun.season,
            ModelRun.season_type,
            ModelRun.week,
            ModelRun.run_at,
            ModelRun.model_version,
        )
        .where(
            ModelRun.kind == "live",
            ModelRun.season == season,
            exists().where(TeamRating.run_id == ModelRun.id),
        )
        .order_by(ModelRun.run_at.desc(), ModelRun.id.desc())
        .limit(1)
    )
    if week is not None:
        query = query.where(ModelRun.week == week)
    if season_type is not None:
        query = query.where(ModelRun.season_type == season_type)
    if before is not None:
        query = query.where(ModelRun.run_at < before)
    row = session.execute(query).first()
    return RunInfo(*row) if row else None


def rating_runs(session: Session, season: int) -> list[RunInfo]:
    """Every live rating run of a season, oldest first (rating history)."""
    query = (
        select(
            ModelRun.id,
            ModelRun.season,
            ModelRun.season_type,
            ModelRun.week,
            ModelRun.run_at,
            ModelRun.model_version,
        )
        .where(
            ModelRun.kind == "live",
            ModelRun.season == season,
            exists().where(TeamRating.run_id == ModelRun.id),
        )
        .order_by(ModelRun.run_at, ModelRun.id)
    )
    return [RunInfo(*row) for row in session.execute(query)]


def last_published_at(session: Session) -> datetime | None:
    return session.scalar(select(func.max(Prediction.published_at)))
