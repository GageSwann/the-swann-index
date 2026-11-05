"""Live rating runs: which run a page shows, its Sunday baseline, and the history."""

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

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


# Movement (rank arrows, biggest movers) compares with the official weekly poll: the last
# run of the most recent Sunday before the shown run's day, Eastern time (Phase 12.5,
# owner's rule, #126). Sunday's run comes after Saturday's games, so on a Sunday the
# arrows show the week's official move (vs. the previous Sunday); Monday to Saturday they
# show the move since that Sunday, with midweek results.
EASTERN = ZoneInfo("America/New_York")
BASELINE_WINDOW = timedelta(days=15)  # runs fetched to find it (a week back, plus gaps)


def baseline_cutoff(run_at: datetime) -> datetime:
    """The end (midnight Eastern) of the most recent Sunday before `run_at`'s Eastern date,
    in UTC: the baseline is the last run before this moment, so a Sunday without a run
    falls back to the latest run before it."""
    day = run_at.astimezone(EASTERN).date()
    since_sunday = (day.weekday() + 1) % 7 or 7  # Mon 1 ... Sat 6, Sun 7 (the previous one)
    monday_after = day - timedelta(days=since_sunday - 1)
    return datetime.combine(monday_after, time(0), tzinfo=EASTERN).astimezone(UTC)


def run_and_baseline(
    session: Session, season: int, week: int | None = None, season_type: str | None = None
) -> tuple[RunInfo | None, RunInfo | None]:
    """The newest rating run (optionally within a week) and its baseline: the last run
    before the end of the most recent Sunday before it (`baseline_cutoff`, any week), in
    one round trip. None for the baseline before the season's first Sunday run."""
    anchor = rating_runs_query(season, ModelRun.run_at)
    if week is not None:
        anchor = anchor.where(ModelRun.week == week)
    if season_type is not None:
        anchor = anchor.where(ModelRun.season_type == season_type)
    latest_at = newest_first(anchor).limit(1).scalar_subquery()
    query = newest_first(
        rating_runs_query(season).where(
            ModelRun.run_at <= latest_at, ModelRun.run_at > latest_at - BASELINE_WINDOW
        )
    )
    runs = [RunInfo(*row) for row in session.execute(query)]
    if not runs:
        return None, None
    cutoff = baseline_cutoff(runs[0].run_at)
    return runs[0], next((r for r in runs[1:] if r.run_at < cutoff), None)


def rating_runs(session: Session, season: int) -> list[RunInfo]:
    """Every live rating run of a season, oldest first (rating history)."""
    query = rating_runs_query(season).order_by(ModelRun.run_at, ModelRun.id)
    return [RunInfo(*row) for row in session.execute(query)]


def run_params(session: Session, run_id: int) -> dict:
    """A run's saved parameters (e.g. `season_hfa`, `resume_benchmark`)."""
    return session.scalar(select(ModelRun.params).where(ModelRun.id == run_id)) or {}
