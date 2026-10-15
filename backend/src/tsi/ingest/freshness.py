"""When is a cached CFBD response still good?

- Finished season (cached after it ended): fresh forever; completed data never changes.
- In-progress season: fresh for a few hours, so a daily run always sees new results.
- No season (e.g. /venues): fresh for a month.

A CFB season Y runs Aug Y through the January title game, so it is treated as
over from Feb 1 of Y+1.
"""

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

LIVE_SEASON_MAX_AGE = timedelta(hours=6)
STATIC_MAX_AGE = timedelta(days=30)


def current_season(now: datetime) -> int:
    """Season in progress (or most recently finished) at `now`: Jan belongs to last season."""
    return now.year if now.month >= 2 else now.year - 1


def season_end(season: int) -> datetime:
    return datetime(season + 1, 2, 1, tzinfo=UTC)


def is_fresh(params: Mapping[str, Any], fetched_at: datetime, now: datetime) -> bool:
    season = params.get("year")
    if season is None:
        return now - fetched_at <= STATIC_MAX_AGE
    if fetched_at >= season_end(int(season)):
        return True  # fetched after the season was over: final
    return now - fetched_at <= LIVE_SEASON_MAX_AGE
