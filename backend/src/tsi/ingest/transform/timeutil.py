"""CFBD timestamps -> timezone-aware UTC datetimes.

Kickoff times are the no-look-ahead cutoff, so they must never be naive or
silently shifted into local time.
"""

from datetime import UTC, datetime


def parse_utc(value: str | None) -> datetime | None:
    """'2024-08-30T00:00:00.000Z' -> datetime(2024, 8, 30, 0, 0, tzinfo=UTC)."""
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp without timezone: {value!r}")
    return parsed.astimezone(UTC)
