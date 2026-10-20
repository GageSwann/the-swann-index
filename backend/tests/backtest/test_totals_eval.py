import pytest
from tests.factories import make_pick

from tsi.backtest.totals_eval import summarize_totals
from tsi.backtest.walk_forward import Pick


def pick(gid: int, home: int, away: int, predicted: float) -> Pick:
    return make_pick(gid, home, away, total=predicted)


def test_totals_summary() -> None:
    picks = [pick(1, 30, 20, 55.0), pick(2, 21, 21, 50.0), pick(3, 10, 10, 50.0)]
    closing = {1: 48.0, 2: 45.0}  # game 3 has no closing total: not scored

    s = summarize_totals("x", picks, closing)

    assert s.games == 2
    assert s.mae == pytest.approx((5 + 8) / 2)
    assert s.market_mae == pytest.approx((2 + 3) / 2)
    assert s.bias == pytest.approx((5 + 8) / 2)
    assert s.ou_accuracy == pytest.approx(
        0.5
    )  # game 1: over, right; game 2: over 45 but 42 scored, wrong
