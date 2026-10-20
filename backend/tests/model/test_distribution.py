import math

import numpy as np
import pytest

from tsi.model.distribution import RHO_LIMIT, DistributionParams, ScoreDistribution
from tsi.model.distribution_fit import fit_rho_per_point, fit_total_sigma, normal_cdf
from tsi.model.ratings.probability import win_prob


def test_team_scores_and_their_spread() -> None:
    d = ScoreDistribution(margin=7.0, total=55.0, sigma_margin=15.0, sigma_total=16.0, rho=0.0)

    assert (d.home_points, d.away_points) == (31.0, 24.0)
    assert d.sigma_home == pytest.approx(math.sqrt(15**2 + 16**2) / 2)
    assert d.p_home_over(31.0) == pytest.approx(0.5)
    assert d.p_total_over(55.0) == pytest.approx(0.5)


def test_win_probability_matches_the_margin_model() -> None:
    d = ScoreDistribution(-4.5, 50.0, 15.2, 16.0, 0.0)

    assert d.home_win_prob == pytest.approx(win_prob(-4.5, 15.2))
    assert d.p_margin_over(-3.5) < 0.5  # home +3.5 covers less than half the time


def test_correlation_widens_the_favorite_and_narrows_the_underdog() -> None:
    d = DistributionParams(15.0, 16.0, 0.0, 0.01).for_game(margin=20.0, total=55.0)

    assert d.rho == pytest.approx(0.2)
    assert d.sigma_home > d.sigma_away


def test_rho_is_clipped_and_sigma_total_grows_with_the_total() -> None:
    params = DistributionParams(15.0, 16.0, 0.1, 0.05)

    assert params.for_game(30.0, 55.0).rho == RHO_LIMIT
    assert params.for_game(0.0, 65.0).sigma_total == pytest.approx(17.0)


def test_normal_cdf_matches_erf() -> None:
    z = np.array([-2.5, -1.0, 0.0, 0.3, 1.96])
    expected = [0.5 * (1 + math.erf(v / math.sqrt(2))) for v in z]

    assert normal_cdf(z) == pytest.approx(expected, abs=1e-6)


def test_fit_recovers_known_spread_and_correlation() -> None:
    rng = np.random.default_rng(7)
    n = 20000
    pred_total = rng.uniform(40, 70, n)
    pred_margin = rng.uniform(-25, 25, n)
    rho = np.clip(0.008 * pred_margin, -0.5, 0.5)
    z1, z2 = rng.standard_normal(n), rng.standard_normal(n)
    margin = pred_margin + 15.0 * z1
    total = pred_total + 14.0 * (rho * z1 + np.sqrt(1 - rho**2) * z2)

    base, slope = fit_total_sigma(pred_total, total)
    rho_per_point = fit_rho_per_point(pred_margin, margin, pred_total, total)

    assert base == pytest.approx(14.0, abs=0.4)
    assert slope <= 0.04
    assert rho_per_point == pytest.approx(0.008, abs=0.002)
