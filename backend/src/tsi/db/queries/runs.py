"""Live rating runs: which run a page shows, its predecessor, and the run history."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Select, exists, select
from sqlalchemy.orm import Session

from tsi.db.models import ModelRun, TeamRating


@dataclass(frozen=True)
class RunInfo:
    id: int
    season: int
    season_type: str
    week: int
    run_at: datetime
    model_version: str


RUN_COLUMNS = (
    ModelRun.id,
    ModelRun.season,
    ModelRun.season_type,
    ModelRun.week,
    ModelRun.run_at,
    ModelRun.model_version,
)


def rating_runs_query(season: int, *columns) -> Select:
    """Live runs of a season that stored team ratings (daily `tsi rate`), unordered."""
    return select(*(columns or RUN_COLUMNS)).where(
        ModelRun.kind == "live",
        ModelRun.season == season,
        exists().where(TeamRating.run_id == ModelRun.id),
    )


def newest_first(query: Select) -> Select:
    return query.order_by(ModelRun.run_at.desc(), ModelRun.id.desc())


def run_and_previous(
    session: Session, season: int, week: int | None = None, season_type: str | None = None
) -> tuple[RunInfo | None, RunInfo | None]:
    """The newest rating run (optionally within a week) and the run before it (any week),
    in one round trip. The previous run gives the rankings' day-over-day movement."""
    anchor = rating_runs_query(season, ModelRun.run_at)
    if week is not None:
        anchor = anchor.where(ModelRun.week == week)
    if season_type is not None:
        anchor = anchor.where(ModelRun.season_type == season_type)
    latest_at = newest_first(anchor).limit(1).scalar_subquery()
    query = newest_first(rating_runs_query(season).where(ModelRun.run_at <= latest_at)).limit(2)
    runs = [RunInfo(*row) for row in session.execute(query)]
    return (runs[0] if runs else None, runs[1] if len(runs) > 1 else None)


def rating_runs(session: Session, season: int) -> list[RunInfo]:
    """Every live rating run of a season, oldest first (rating history)."""
    query = rating_runs_query(season).order_by(ModelRun.run_at, ModelRun.id)
    return [RunInfo(*row) for row in session.execute(query)]
