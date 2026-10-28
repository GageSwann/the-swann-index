"""Live rating runs: which run a page shows, the run a week before it, and the history."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import Select, exists, func, or_, select
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


# Movement compares with the newest run at least this much older: about a week, with
# slack for the nightly job's start time drifting by a few hours (decision #79).
WEEK_AGO = timedelta(days=6)


def run_and_week_ago(
    session: Session, season: int, week: int | None = None, season_type: str | None = None
) -> tuple[RunInfo | None, RunInfo | None]:
    """The newest rating run (optionally within a week) and the newest run at least
    `WEEK_AGO` before it (any week), in one round trip: the rankings' weekly movement.
    Daily runs barely move between game days, so day-over-day change shows little."""
    anchor = rating_runs_query(season, ModelRun.run_at)
    if week is not None:
        anchor = anchor.where(ModelRun.week == week)
    if season_type is not None:
        anchor = anchor.where(ModelRun.season_type == season_type)
    latest_at = newest_first(anchor).limit(1).scalar_subquery()
    week_ago_at = (
        rating_runs_query(season, func.max(ModelRun.run_at))
        .where(ModelRun.run_at <= latest_at - WEEK_AGO)
        .scalar_subquery()
    )
    query = newest_first(
        rating_runs_query(season).where(
            or_(ModelRun.run_at == latest_at, ModelRun.run_at == week_ago_at)
        )
    )
    runs = [RunInfo(*row) for row in session.execute(query)]
    if not runs:
        return None, None
    return runs[0], next((r for r in runs[1:] if r.run_at < runs[0].run_at), None)


def rating_runs(session: Session, season: int) -> list[RunInfo]:
    """Every live rating run of a season, oldest first (rating history)."""
    query = rating_runs_query(season).order_by(ModelRun.run_at, ModelRun.id)
    return [RunInfo(*row) for row in session.execute(query)]


def run_params(session: Session, run_id: int) -> dict:
    """A run's saved parameters (e.g. `season_hfa`, `resume_benchmark`)."""
    return session.scalar(select(ModelRun.params).where(ModelRun.id == run_id)) or {}
