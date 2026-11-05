"""Learn the key-number weights from walk-forward predictions (decision #118).

Iterative proportional fitting: start every weight at 1, then repeatedly scale each one
by (observed count + s) / (expected count under the current weights + s), where s pulls
rare values toward 1. Margins fold to |k| and keep only the spikes (each weight over its
local average); a tie gets weight 0 (college football has no ties). Pure.
"""

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from tsi.model.key_numbers import (
    MARGIN_WEIGHTS,
    MARGINS,
    TOTALS,
    KeyNumbers,
    as_weights,
)

SHRINK = 30.0  # pseudo-count toward weight 1
ITERATIONS = 8
SPIKE_HALF_WIDTH = 3  # the local average for margin spikes: |k| - 3 .. |k| + 3


def fit_key_numbers(
    margins: Sequence[tuple[float, float, int]],  # (predicted margin, sigma, actual margin)
    totals: Sequence[tuple[float, float, int]],  # (predicted total, sigma, actual total)
) -> KeyNumbers:
    margin = _spikes(_fit_margin(margins))
    total = _fit(
        totals, lambda m, s: KeyNumbers.none().total_table(m, s).probs, TOTALS, lambda v: v
    )
    return KeyNumbers(as_weights(margin), as_weights(total))


def _fit_margin(samples: Sequence[tuple[float, float, int]]) -> NDArray[np.float64]:
    def base(mean: float, sigma: float) -> NDArray[np.float64]:
        p = KeyNumbers.none().margin_table(mean, sigma).probs.copy()
        p[MARGINS == 0] = 0.0  # no ties
        return p

    w = _fit(samples, base, MARGINS, lambda v: min(abs(v), MARGIN_WEIGHTS - 1))
    w[0] = 0.0
    return w


def _fit(samples, base, values, fold) -> NDArray[np.float64]:
    groups = np.array([fold(int(v)) for v in values])
    size = groups.max() + 1
    observed = np.bincount(
        [fold(int(a)) for _, _, a in samples if values[0] <= a <= values[-1]], minlength=size
    ).astype(float)
    bases = [base(m, s) for m, s, _ in samples]
    w = np.ones(size)
    for _ in range(ITERATIONS):
        expected = np.zeros(size)
        for b in bases:
            q = b * w[groups]
            expected += np.bincount(groups, q / q.sum(), minlength=size)
        w *= (observed + SHRINK) / (expected + SHRINK)
    return w


def _spikes(w: NDArray[np.float64]) -> NDArray[np.float64]:
    """Each margin weight over its local average: the key-number shape without the tails."""
    out = w.copy()
    for i in range(1, len(w)):
        window = w[max(1, i - SPIKE_HALF_WIDTH) : i + SPIKE_HALF_WIDTH + 1]
        out[i] = w[i] / window.mean()
    out[0] = 0.0
    return out
