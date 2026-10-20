from datetime import UTC, datetime

import pytest

from tsi.backtest.book_eval import simulate_book, summarize_book
from tsi.backtest.walk_forward import Pick
from tsi.book.edges import EdgeShrink
from tsi.db.queries.market import OpeningLine
from tsi.db.queries.results import GameResult
from tsi.model.distribution import DistributionParams

PARAMS = DistributionParams(15.4, 16.4, 0.0, 0.0)
SHRINK = EdgeShrink(k_spread=0.0, k_total=0.3)


def pick(gid: int, home: int, away: int, total: float) -> Pick:
    kickoff = datetime(2024, 9, 7, tzinfo=UTC)
    g = GameResult(gid, 2024, kickoff, 1, 2, "fbs", "fbs", False, home, away)
    return Pick(g, 0.0, 0.0, total, True, 4, (), ())


def test_book_bets_the_opener_and_measures_clv_at_the_close() -> None:
    picks = [
        pick(1, 35, 30, 58.0),  # TSI 58 vs. opener 48: over, 65 scored -> win
        pick(2, 10, 7, 38.0),  # TSI 38 vs. 48: under, 17 scored -> win
        pick(3, 30, 30, 49.0),  # 1 point off: no pick
        pick(4, 30, 30, 70.0),  # no opener: never bet
    ]
    opening = {i: OpeningLine(-3.0, 48.0) for i in (1, 2, 3)}

    bets = simulate_book(picks, PARAMS, SHRINK, opening, {}, {1: 50.0, 2: 46.0})

    assert [(b.side, b.result) for b in bets] == [("over", "win"), ("under", "win")]
    assert [b.clv for b in bets] == [pytest.approx(2.0), pytest.approx(2.0)]  # both beat the close
    assert all(b.units == pytest.approx(100 / 110) for b in bets)


def test_summary_by_market_and_tier() -> None:
    picks = [pick(1, 35, 30, 58.0), pick(2, 30, 30, 40.0)]  # over wins, under loses (60 > 48)
    opening = {1: OpeningLine(None, 48.0), 2: OpeningLine(None, 48.0)}
    bets = simulate_book(picks, PARAMS, SHRINK, opening, {}, {})

    records = summarize_book("x", bets)
    total = next(r for r in records if r.tier == 0)

    assert (total.wins, total.losses, total.bets) == (1, 1, 2)
    assert total.win_rate == 0.5
    assert total.roi == pytest.approx((100 / 110 - 1) / 2)
    assert total.clv is None  # no closing totals given
