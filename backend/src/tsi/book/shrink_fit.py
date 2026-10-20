"""Learn how far to trust TSI over the market line (k in `book/edges.py`).

For past games: z = (TSI mean - line mean) / sigma, outcome = the home side
covered (or the game went over). k minimizes log loss of Phi(k * z); pushes are
left out. k = 0 means TSI adds nothing to the line, k = 1 means trust TSI fully.
"""

from collections.abc import Sequence

import numpy as np

from tsi.model.distribution_fit import normal_cdf
from tsi.model.ratings.probability import golden_min

K_RANGE = (0.0, 1.5)


def fit_k(z: Sequence[float], outcome: Sequence[float]) -> float:
    """`z`: standardized TSI-minus-line; `outcome`: 1 if the actual result beat the line."""
    zs, ys = np.asarray(z, float), np.asarray(outcome, float)
    if len(zs) == 0:
        return 0.0

    def loss(k: float) -> float:
        p = np.clip(normal_cdf(k * zs), 1e-12, 1 - 1e-12)
        return float(-np.mean(ys * np.log(p) + (1 - ys) * np.log(1 - p)))

    k = golden_min(loss, *K_RANGE, tol=0.001)
    return 0.0 if loss(0.0) <= loss(k) else k
