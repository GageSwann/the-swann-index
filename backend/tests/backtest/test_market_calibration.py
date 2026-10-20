import pytest
from tests.factories import make_pick

from tsi.backtest.market_calibration import (
    line_calibration,
    line_check,
    spread_samples,
    total_samples,
)
from tsi.backtest.walk_forward import Pick
from tsi.model.distribution import DistributionParams

PARAMS = DistributionParams(15.0, 16.0, 0.0, 0.0)


def pick(gid: int, home: int, away: int, margin: float, total: float, season=2024) -> Pick:
    return make_pick(gid, home, away, margin=margin, total=total, season=season)


def test_spread_samples_are_home_view_and_skip_pushes() -> None:
    # TSI home by 10, line home -3: z > 0; home won by 7 -> covered. Game 2 pushes at -3.
    picks = [pick(1, 27, 20, 10.0, 47.0), pick(2, 20, 17, 10.0, 37.0), pick(3, 7, 0, 1.0, 7.0)]

    samples = spread_samples(picks, PARAMS, {1: -3.0, 2: -3.0, 3: None})

    assert len(samples) == 1
    assert samples[0].z == pytest.approx(7 / 15) and samples[0].outcome == 1.0


def test_total_samples() -> None:
    samples = total_samples([pick(1, 30, 30, 0.0, 50.0)], PARAMS, {1: 55.0})

    assert samples[0].z == pytest.approx(-5 / 16) and samples[0].outcome == 1.0


def test_zero_k_puts_everything_at_fifty_percent() -> None:
    samples = spread_samples([pick(1, 27, 20, 10.0, 47.0)], PARAMS, {1: -3.0})

    bins = line_calibration(samples, 0.0)

    assert bins[0].predicted == pytest.approx(0.5)


def test_line_check_fits_on_train_and_scores_validation() -> None:
    train = [pick(i, 30, 20, 10.0, 50.0, 2018) for i in range(1, 30)]
    validate = [pick(100, 30, 20, 10.0, 50.0, 2024)]
    spreads = {i: -3.0 for i in range(1, 30)} | {100: -3.0}

    check = line_check(train, validate, PARAMS, spreads, {})

    assert check.shrink.k_spread > 0  # TSI liked home every time and home always covered
    assert check.shrink.k_total == 0.0  # no totals: trust the line
    assert sum(b.games for b in check.cover) == 1 and check.over == []
