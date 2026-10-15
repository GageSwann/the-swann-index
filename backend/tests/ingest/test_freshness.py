from datetime import UTC, datetime, timedelta

import pytest

from tsi.ingest.freshness import LIVE_SEASON_MAX_AGE, current_season, is_fresh

OCT_14_2026 = datetime(2026, 10, 14, 21, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("now", "season"),
    [
        (datetime(2026, 10, 14, tzinfo=UTC), 2026),
        (datetime(2027, 1, 12, tzinfo=UTC), 2026),  # title game month belongs to 2026
        (datetime(2027, 2, 1, tzinfo=UTC), 2027),
        (datetime(2026, 8, 1, tzinfo=UTC), 2026),
    ],
)
def test_current_season(now: datetime, season: int) -> None:
    assert current_season(now) == season


def test_finished_season_cached_after_it_ended_is_fresh_forever() -> None:
    fetched = datetime(2026, 10, 14, tzinfo=UTC)
    much_later = fetched + timedelta(days=3650)

    assert is_fresh({"year": 2024}, fetched, much_later)


def test_live_season_expires_within_a_day() -> None:
    fetched = OCT_14_2026 - LIVE_SEASON_MAX_AGE - timedelta(minutes=1)

    assert not is_fresh({"year": 2026}, fetched, OCT_14_2026)
    assert is_fresh({"year": 2026}, OCT_14_2026 - timedelta(hours=1), OCT_14_2026)


def test_season_cached_before_it_ended_is_refetched_after() -> None:
    # Cached mid-January (before the title game) must not be frozen as final.
    fetched = datetime(2027, 1, 10, tzinfo=UTC)
    later = datetime(2027, 3, 1, tzinfo=UTC)

    assert not is_fresh({"year": 2026}, fetched, later)


def test_seasonless_endpoint_lasts_a_month() -> None:
    assert is_fresh({}, OCT_14_2026 - timedelta(days=29), OCT_14_2026)
    assert not is_fresh({}, OCT_14_2026 - timedelta(days=31), OCT_14_2026)
