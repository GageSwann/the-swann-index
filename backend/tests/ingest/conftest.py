from datetime import datetime

import pytest

from tsi.ingest.ledger import CallRecord


class FakeLedger:
    """In-memory stand-in for DbCallLedger."""

    def __init__(self, used: int = 0) -> None:
        self.used = used
        self.records: list[CallRecord] = []

    def calls_this_month(self, now: datetime) -> int:
        return self.used + sum(not r.from_cache for r in self.records)

    def record(self, entry: CallRecord) -> None:
        self.records.append(entry)


@pytest.fixture
def ledger() -> FakeLedger:
    return FakeLedger()
