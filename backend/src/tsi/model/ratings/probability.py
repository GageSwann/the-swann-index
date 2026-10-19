"""Margin -> win probability via a normal margin distribution (refined in Phase 3).

sigma is chosen to minimize log loss on TRAIN games (`fit_sigma`), not taken from
the raw residual spread: a few huge blowouts inflate the residual standard
deviation and make every probability too timid (favorites then win more often
than predicted).
"""

import math
from collections.abc import Sequence

SIGMA_RANGE = (5.0, 40.0)


def win_prob(margin: float, sigma: float) -> float:
    """P(home wins) when the final margin ~ Normal(margin, sigma)."""
    return 0.5 * (1.0 + math.erf(margin / (sigma * math.sqrt(2.0))))


def fit_sigma(pred: Sequence[float], actual: Sequence[float], tol: float = 0.01) -> float:
    """sigma minimizing win/loss log loss (golden-section search; log loss is unimodal here)."""
    outcomes = [1.0 if a > 0 else 0.0 if a < 0 else 0.5 for a in actual]

    def loss(sigma: float) -> float:
        total = 0.0
        for m, o in zip(pred, outcomes, strict=True):
            p = min(max(win_prob(m, sigma), 1e-12), 1 - 1e-12)
            total -= o * math.log(p) + (1 - o) * math.log(1 - p)
        return total

    lo, hi = SIGMA_RANGE
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
