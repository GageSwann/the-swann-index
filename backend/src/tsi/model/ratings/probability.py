"""Margin -> win probability via a normal margin distribution.

sigma is chosen to minimize log loss on TRAIN games (`fit_sigma`), not taken from
the raw residual spread: a few huge blowouts inflate the residual standard
deviation and make every probability too timid (favorites then win more often
than predicted). The full score distribution is model/distribution.py.
"""

import math
from collections.abc import Callable, Sequence

import numpy as np

SIGMA_RANGE = (5.0, 40.0)
_erf_ufunc = np.frompyfunc(math.erf, 1, 1)  # exact erf, elementwise (numpy has none)


def erf(x: np.ndarray) -> np.ndarray:
    return _erf_ufunc(x).astype(float)


def win_prob(margin: float, sigma: float) -> float:
    """P(home wins) when the final margin ~ Normal(margin, sigma)."""
    return 0.5 * (1.0 + math.erf(margin / (sigma * math.sqrt(2.0))))


def golden_min(loss: Callable[[float], float], lo: float, hi: float, tol: float = 0.01) -> float:
    """Minimizer of a unimodal function on [lo, hi] (golden-section search)."""
    ratio = (math.sqrt(5) - 1) / 2
    a, b = hi - ratio * (hi - lo), lo + ratio * (hi - lo)
    while hi - lo > tol:
        if loss(a) < loss(b):
            hi, b = b, a
            a = hi - ratio * (hi - lo)
        else:
            lo, a = a, b
            b = lo + ratio * (hi - lo)
    return (lo + hi) / 2


def fit_sigma(pred: Sequence[float], actual: Sequence[float], tol: float = 0.01) -> float:
    """sigma minimizing win/loss log loss (log loss is unimodal in sigma here)."""
    margins = np.asarray(pred, dtype=float)
    outcomes = np.sign(np.asarray(actual, dtype=float)) * 0.5 + 0.5  # win 1, loss 0, tie 0.5

    def loss(sigma: float) -> float:
        p = np.clip(0.5 * (1.0 + erf(margins / (sigma * math.sqrt(2.0)))), 1e-12, 1 - 1e-12)
        return float(-np.sum(outcomes * np.log(p) + (1 - outcomes) * np.log(1 - p)))

    return golden_min(loss, *SIGMA_RANGE, tol)
