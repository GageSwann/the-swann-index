"""The calendar week in play, and the site's freshness facts in a single round trip."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from tsi.db.models import CalendarWeek, ModelRun, Prediction
from tsi.db.queries.runs import newest_first, rating_runs_query


def _latest_week(season: int, now: datetime, column) -> Select:
    return (
        select(column)
        .where(CalendarWeek.season == season, CalendarWeek.start_date <= now)
        .order_by(CalendarWeek.start_date.desc())
        .limit(1)
    )


def calendar_week(session: Session, season: int, now: datetime) -> tuple[str, int]:
    """(season_type, week) of the latest calendar week that has started; ('regular', 0) before."""
    row = session.execute(
        _latest_week(season, now, CalendarWeek.season_type).add_columns(CalendarWeek.week)
    ).first()
    return (row[0], row[1]) if row else ("regular", 0)


@dataclass(frozen=True)
class Freshness:
    season_type: str
    week: int
    ratings_at: datetime | None  # latest daily rating run
    model_version: str | None  # of that run
    published_at: datetime | None  # latest prediction snapshot


def freshness(session: Session, season: int, now: datetime) -> Freshness:
    """Week in play, latest rating run and latest snapshot: one statement of subqueries."""

    def latest_run(column):
        return newest_first(rating_runs_query(season, column)).limit(1).scalar_subquery()

    row = session.execute(
        select(
            _latest_week(season, now, CalendarWeek.season_type).scalar_subquery(),
            _latest_week(season, now, CalendarWeek.week).scalar_subquery(),
            latest_run(ModelRun.run_at),
            latest_run(ModelRun.model_version),
            select(func.max(Prediction.published_at)).scalar_subquery(),
        )
    ).one()
    season_type, week, ratings_at, version, published = row
    return Freshness(season_type or "regular", week or 0, ratings_at, version, published)
