"""Fit the score distribution's spread and correlation on backtest residuals.

- sigma_margin: the win-probability sigma (log loss at threshold 0, decision #34)
- sigma_total (base + slope): minimize log loss of P(total > pred + d) over offsets
  d around the projection, i.e. calibrate the CDF where lines sit rather than use
  the residual standard deviation (which blowouts inflate)
- rho_per_point: E[z_margin * z_total] = rho_per_point * margin, least squares
  through the origin on standardized residuals
"""

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from tsi.model.distribution import MIN_SIGMA, TOTAL_PIVOT, DistributionParams
from tsi.model.ratings.probability import golden_min

OFFSETS = (-14.0, -10.0, -7.0, -3.0, 3.0, 7.0, 10.0, 14.0)
SLOPES = tuple(round(0.02 * i, 2) for i in range(21))  # 0.00 .. 0.40
Array = NDArray[np.float64]


def fit_distribution(
    sigma_margin: float,
    pred_margin: Sequence[float],
    actual_margin: Sequence[float],
    pred_total: Sequence[float],
    actual_total: Sequence[float],
) -> DistributionParams:
    pm, am = np.asarray(pred_margin, float), np.asarray(actual_margin, float)
    pt, at = np.asarray(pred_total, float), np.asarray(actual_total, float)
    base, slope = fit_total_sigma(pt, at)
    return DistributionParams(sigma_margin, base, slope, fit_rho_per_point(pm, am, pt, at))


def fit_total_sigma(pred: Array, actual: Array) -> tuple[float, float]:
    """(base, slope) for sigma = base + slope * (pred - TOTAL_PIVOT); slope on a grid."""
    best: tuple[float, float, float] | None = None
    for slope in SLOPES:
        offset = slope * (pred - TOTAL_PIVOT)

        def loss(base: float, offset: Array = offset) -> float:
            return threshold_log_loss(pred, actual, np.maximum(MIN_SIGMA, base + offset))

        base = golden_min(loss, MIN_SIGMA, 40.0)
        value = loss(base)
        if best is None or value < best[0]:
            best = (value, base, slope)
    assert best is not None
    return best[1], best[2]


def fit_rho_per_point(
    pred_margin: Array, actual_margin: Array, pred_total: Array, actual_total: Array
) -> float:
    rm, rt = actual_margin - pred_margin, actual_total - pred_total
    product = (rm / rm.std()) * (rt / rt.std())
    return float(np.dot(pred_margin, product) / np.dot(pred_margin, pred_margin))


def threshold_log_loss(pred: Array, actual: Array, sigma: Array) -> float:
    """Mean log loss of P(actual > pred + d) = 1 - Phi(d / sigma) over OFFSETS."""
    total = 0.0
    for d in OFFSETS:
        p = np.clip(1.0 - normal_cdf(d / sigma), 1e-12, 1 - 1e-12)
        hit = actual > pred + d
        total -= float(np.mean(np.where(hit, np.log(p), np.log(1 - p))))
    return total / len(OFFSETS)


def normal_cdf(z: Array) -> Array:
    """Vectorized standard normal CDF (Abramowitz & Stegun 7.1.26, error < 1.5e-7)."""
    x = np.abs(z) / np.sqrt(2.0)
    t = 1.0 / (1.0 + 0.3275911 * x)
    poly = t * (
        0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429)))
    )
    erf = 1.0 - poly * np.exp(-x * x)
    return 0.5 * (1.0 + np.sign(z) * erf)
