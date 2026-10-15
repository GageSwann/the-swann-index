from datetime import UTC, datetime

from tsi.ingest.ledger import month_start


def test_month_start_truncates_to_first_of_month() -> None:
    now = datetime(2026, 10, 14, 20, 45, 13, 123, tzinfo=UTC)

    assert month_start(now) == datetime(2026, 10, 1, tzinfo=UTC)
