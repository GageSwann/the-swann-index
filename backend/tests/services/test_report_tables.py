from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from tsi.backtest.book_eval import GradedBet
from tsi.services.report_tables import book_units


def bet(day: int, units: float, kelly: float, hour: int = 18) -> GradedBet:
    kickoff = datetime(2023, 9, day, hour, tzinfo=UTC)
    return GradedBet(2023, kickoff, "total", "over", 1, "win", units, 1.0, kelly, 0.5)


def test_book_units_accumulates_by_day_in_kickoff_order() -> None:
    book = SimpleNamespace(bets=[bet(9, -1.0, -1.5), bet(2, 0.91, 1.2), bet(2, 0.91, 0.8, hour=23)])

    rows = book_units(book)  # type: ignore[arg-type]

    assert [r["date"] for r in rows] == ["2023-09-02", "2023-09-09"]
    assert rows[0]["units"] == pytest.approx(1.82)
    assert rows[0]["kelly_units"] == pytest.approx(2.0)
    assert rows[1]["units"] == pytest.approx(0.82)
    assert rows[1]["season"] == 2023
