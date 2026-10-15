"""Weighted ridge regression where some columns (intercept, HFA) are not penalized.

Solves  min_b  sum_i w_i (y_i - x_i b)^2 + lam * sum_{j penalized} b_j^2
via the normal equations  (X'WX + lam*P) b = X'Wy.  Small dense problems only
(a few hundred columns), so a direct solve is fast and exact.

Unpenalized columns get a negligible `JITTER` so the system stays solvable when
a column carries no information yet (e.g. HFA when every game so far was at a
neutral site); such a coefficient then comes out as 0.
"""

import numpy as np
from numpy.typing import NDArray

JITTER = 1e-8


def weighted_ridge(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
    weights: NDArray[np.float64],
    lam: float,
    penalized: NDArray[np.bool_],
) -> NDArray[np.float64]:
    xw = x * weights[:, None]
    gram = x.T @ xw
    gram[np.diag_indices_from(gram)] += np.where(penalized, lam, JITTER)
    return np.linalg.solve(gram, xw.T @ y)
