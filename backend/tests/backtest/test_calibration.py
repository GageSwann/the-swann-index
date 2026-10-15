import pytest

from tsi.backtest.calibration import calibration_table


def test_bins_use_the_favorites_perspective() -> None:
    # Home 30% (away is the 70% favorite and wins) counts like a 70% favorite winning.
    bins = calibration_table([0.3, 0.75, 0.72, 0.55], [0, 1, 0, 1])

    seventy = next(b for b in bins if b.low == 0.7)
    assert seventy.games == 3
    assert seventy.predicted == pytest.approx((0.7 + 0.75 + 0.72) / 3)
    assert seventy.observed == pytest.approx(2 / 3)


def test_perfectly_calibrated_bin_is_within_tolerance() -> None:
    bins = calibration_table([0.6] * 10, [1] * 6 + [0] * 4)

    assert bins[0].observed == pytest.approx(0.6)
    assert bins[0].within_tolerance


def test_certain_predictions_land_in_the_top_bin() -> None:
    assert calibration_table([1.0], [1])[0].high == 1.0
