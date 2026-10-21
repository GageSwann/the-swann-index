"""`/meta/current`: what season and week it is, and how fresh the data is."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from tsi.db.queries.runs import last_published_at, latest_rating_run
from tsi.ingest.freshness import current_season
from tsi.model.config import MODEL_VERSION
from tsi.services.rate_store import calendar_week


@dataclass(frozen=True)
class Meta:
    season: int
    season_type: str
    week: int  # latest calendar week that has started (0 before the season)
    ratings_updated_at: datetime | None  # latest daily rating run
    predictions_published_at: datetime | None  # latest snapshot
    model_version: str


def current_meta(session: Session, now: datetime) -> Meta:
    season = current_season(now)
    season_type, week = calendar_week(session, season, now)
    run = latest_rating_run(session, season)
    return Meta(
        season=season,
        season_type=season_type,
        week=week,
        ratings_updated_at=run.run_at if run else None,
        predictions_published_at=last_published_at(session),
        model_version=run.model_version if run else MODEL_VERSION,
    )
