"""Margin -> win probability via a normal margin distribution (refined in Phase 3)."""

import math
from collections.abc import Sequence


def win_prob(margin: float, sigma: float) -> float:
    """P(home wins) when the final margin ~ Normal(margin, sigma)."""
    return 0.5 * (1.0 + math.erf(margin / (sigma * math.sqrt(2.0))))


def residual_sigma(pred: Sequence[float], actual: Sequence[float]) -> float:
    """Standard deviation of prediction errors (fit on train seasons only)."""
    errors = [a - p for p, a in zip(pred, actual, strict=True)]
    mean = sum(errors) / len(errors)
    return math.sqrt(sum((e - mean) ** 2 for e in errors) / (len(errors) - 1))
