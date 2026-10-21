"""`/meta/current`: what season and week it is, and how fresh the data is."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from tsi.db.queries.calendar import freshness
from tsi.ingest.freshness import current_season
from tsi.model.config import MODEL_VERSION


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
    f = freshness(session, season, now)
    return Meta(
        season=season,
        season_type=f.season_type,
        week=f.week,
        ratings_updated_at=f.ratings_at,
        predictions_published_at=f.published_at,
        model_version=f.model_version or MODEL_VERSION,
    )
