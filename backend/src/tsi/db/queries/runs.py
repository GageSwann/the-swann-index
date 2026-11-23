"""Live rating runs: which run a page shows, its Sunday baseline, and the history."""

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import Select, exists, func, select
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


# Movement (rank arrows, biggest movers) shows the official weekly poll's move all week:
# the shown run against the last run of the Sunday before the latest Sunday (Eastern
# time). Sunday's run comes after Saturday's games, so every day from that Sunday to the
# next Saturday compares with the previous Sunday; midweek results move the current rank,
# never the baseline (owner's rule #126, changed by #156: Monday no longer resets to 0).
EASTERN = ZoneInfo("America/New_York")
BASELINE_WINDOW = timedelta(days=21)  # runs fetched to find it (up to 13 days back, plus gaps)


def baseline_cutoff(run_at: datetime) -> datetime:
    """The end (midnight Eastern) of the Sunday before the latest Sunday on or before
    `run_at`'s Eastern date, in UTC: the baseline is the last run before this moment, so a
    Sunday without a run falls back to the latest run before it."""
    day = run_at.astimezone(EASTERN).date()
    poll_sunday = day - timedelta(days=(day.weekday() + 1) % 7)  # Sun 0, Mon 1 ... Sat 6
    monday_after_previous = poll_sunday - timedelta(days=6)
    return datetime.combine(monday_after_previous, time(0), tzinfo=EASTERN).astimezone(UTC)


def run_and_baseline(
    session: Session, season: int, week: int | None = None, season_type: str | None = None
) -> tuple[RunInfo | None, RunInfo | None]:
    """The newest rating run (optionally within a week) and its baseline: the last run
    at the end of the previous week's Sunday poll (`baseline_cutoff`, any week), in
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


def latest_rating_run(session: Session, season: int) -> RunInfo | None:
    """The newest live rating run of a season (the one pages show)."""
    row = session.execute(newest_first(rating_runs_query(season)).limit(1)).first()
    return None if row is None else RunInfo(*row)


@dataclass(frozen=True)
class HistoryPoint:
    """One team in one rating run: what its rating chart needs, and nothing more."""

    run_at: datetime
    week: int
    rating: float | None  # season set; None when the run has no season rating for it
    rank_power: int | None
    rank_resume: int | None
    predictive_rating: float | None


def rating_history(session: Session, season: int, team_id: int) -> list[HistoryPoint]:
    """Every live rating run of a season with this team's chart values, oldest first: one
    compact row per run (the full rows of both rating sets cost ~5x more, #154)."""
    season_row = TeamRating.basis == "season"
    query = (
        select(
            ModelRun.run_at,
            ModelRun.week,
            func.max(TeamRating.rating).filter(season_row),
            func.max(TeamRating.rank_power).filter(season_row),
            func.max(TeamRating.rank_resume).filter(season_row),
            func.max(TeamRating.rating).filter(TeamRating.basis == "predictive"),
        )
        .join(TeamRating, TeamRating.run_id == ModelRun.id)
        .where(
            ModelRun.kind == "live",
            ModelRun.season == season,
            TeamRating.team_id == team_id,
            TeamRating.variant == "raw",
        )
        .group_by(ModelRun.id)
        .order_by(ModelRun.run_at, ModelRun.id)
    )
    return [HistoryPoint(*row) for row in session.execute(query)]
