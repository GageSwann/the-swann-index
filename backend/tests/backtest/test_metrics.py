import math

import pytest

from tsi.backtest.metrics import brier, log_loss, mae, rmse, straight_up_accuracy


def test_mae_and_rmse() -> None:
    assert mae([3, -7], [10, -3]) == pytest.approx(5.5)
    assert rmse([3, -7], [10, -3]) == pytest.approx(math.sqrt((49 + 16) / 2))


def test_straight_up_counts_pickem_as_half() -> None:
    assert straight_up_accuracy([5, -3, 0, 2], [10, 4, 7, 1]) == pytest.approx(
        (1 + 0 + 0.5 + 1) / 4
    )


def test_brier_and_log_loss() -> None:
    assert brier([0.8, 0.3], [1, 0]) == pytest.approx((0.04 + 0.09) / 2)
    assert log_loss([0.5], [1]) == pytest.approx(math.log(2))
    assert math.isfinite(log_loss([1.0], [0]))  # clipped, never infinite
