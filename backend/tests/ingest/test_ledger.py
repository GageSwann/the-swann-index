from datetime import UTC, datetime

from tsi.ingest.ledger import _as_int, month_start


def test_month_start_truncates_to_first_of_month() -> None:
    now = datetime(2026, 10, 14, 20, 45, 13, 123, tzinfo=UTC)

    assert month_start(now) == datetime(2026, 10, 1, tzinfo=UTC)


def test_as_int_handles_strings_and_junk() -> None:
    assert _as_int("2024") == 2024
    assert _as_int(None) is None
    assert _as_int("regular") is None
