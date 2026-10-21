"""Request dependencies: a database session per request, and "now" (overridable in tests)."""

from collections.abc import Iterator
from datetime import UTC, datetime

from fastapi import Request
from sqlalchemy.orm import Session

from tsi.ingest.freshness import current_season


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.sessions() as session:
        yield session


def get_now() -> datetime:
    return datetime.now(UTC)


def season_or_current(season: int | None, now: datetime) -> int:
    return season if season is not None else current_season(now)
