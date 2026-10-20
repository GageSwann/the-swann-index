from datetime import UTC, datetime

import pytest

from tsi.book.consensus import consensus, no_vig
from tsi.db.queries.market import LineSnapshot

NOW = datetime(2026, 10, 19, tzinfo=UTC)


def snap(provider, spread, total, home_ml=None, away_ml=None) -> LineSnapshot:
    return LineSnapshot(1, provider, spread, total, home_ml, away_ml, NOW)


def test_no_vig_normalizes_the_two_prices() -> None:
    home, away = no_vig(-110, -110)
    assert (home, away) == (pytest.approx(0.5), pytest.approx(0.5))

    home, away = no_vig(-200, 170)
    assert home + away == pytest.approx(1.0)
    assert home == pytest.approx((200 / 300) / (200 / 300 + 100 / 270))


def test_consensus_takes_the_median_line_and_averages_no_vig_probabilities() -> None:
    line = consensus(
        [
            snap("A", -3.0, 50.5, -150, 130),
            snap("B", -3.5, 51.0, -160, 135),
            snap("C", -10.0, 51.5),  # stale outlier spread, no moneyline
        ]
    )

    assert line.spread == -3.5 and line.total == 51.0 and line.books == 3
    assert line.home_ml == -155 and line.away_ml == 132
    expected = (no_vig(-150, 130)[0] + no_vig(-160, 135)[0]) / 2
    assert line.home_prob == pytest.approx(expected)


def test_consensus_without_lines() -> None:
    line = consensus([snap("A", None, None)])

    assert line.spread is None and line.total is None and line.home_prob is None
