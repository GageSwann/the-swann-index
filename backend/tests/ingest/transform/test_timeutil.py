from datetime import UTC, datetime

import pytest

from tsi.ingest.transform.timeutil import parse_utc


def test_parses_cfbd_zulu_timestamp_as_utc() -> None:
    assert parse_utc("2024-08-30T00:00:00.000Z") == datetime(2024, 8, 30, tzinfo=UTC)


def test_converts_offsets_to_utc() -> None:
    parsed = parse_utc("2024-08-29T18:00:00-06:00")

    assert parsed == datetime(2024, 8, 30, tzinfo=UTC)
    assert parsed.tzinfo is UTC


def test_empty_is_none() -> None:
    assert parse_utc(None) is None
    assert parse_utc("") is None


def test_naive_timestamp_is_rejected() -> None:
    # A naive time would silently shift the look-ahead cutoff.
    with pytest.raises(ValueError, match="without timezone"):
        parse_utc("2024-08-30T00:00:00")
