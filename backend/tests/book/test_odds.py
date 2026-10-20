import pytest

from tsi.book.config import STANDARD_HOLD
from tsi.book.odds import american_from_prob, prob_from_american, profit_per_unit, vigged_american


def test_fair_odds_formula() -> None:
    assert american_from_prob(0.5) == -100
    assert american_from_prob(0.75) == -300
    assert american_from_prob(0.25) == 300
    assert american_from_prob(0.2) == 400


def test_odds_round_trip() -> None:
    for odds in (-300, -110, 150, 400):
        assert american_from_prob(prob_from_american(odds)) == odds


def test_standard_hold_is_minus_110_both_ways() -> None:
    assert vigged_american(0.5, STANDARD_HOLD) == -110
    implied = 2 * prob_from_american(-110)
    assert 1 - 1 / implied == pytest.approx(STANDARD_HOLD)


def test_extremes_are_capped() -> None:
    assert american_from_prob(1.0) < -100_000
    assert american_from_prob(0.0) > 100_000
    assert vigged_american(0.999, 0.045) == -19900


def test_profit_per_unit() -> None:
    assert profit_per_unit(-110) == pytest.approx(100 / 110)
    assert profit_per_unit(250) == pytest.approx(2.5)
