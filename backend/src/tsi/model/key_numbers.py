"""Key numbers: whole-number margins and totals (doc 05 §1 v2, decision #118).

The bivariate normal (`model/distribution.py`) is smooth, but football scores are not:
margins land on 3 and 7 far more often than on 2 or 9, games never end tied, and totals
cluster on numbers like 41, 44, 51 and 55. Each game's margin and total become
probability tables over whole numbers:

    P(margin = k) ∝ normal mass on [k - 0.5, k + 0.5] × margin_weight[|k|]   (k ≠ 0)
    P(total = t)  ∝ normal mass on [t - 0.5, t + 0.5] × total_weight[t]

The weights are learned from history (`key_numbers_fit.py`): for margins only the
key-number spikes (each weight over its local average), so the tails stay the normal's;
for totals the full weights. Whole-number lines then carry a push probability. Pure.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

MAX_MARGIN = 90  # |margin| support; the weights cover 0..MARGIN_WEIGHTS-1, then 1
MARGIN_WEIGHTS = 61
MAX_TOTAL = 160  # totals 0..MAX_TOTAL

MARGINS = np.arange(-MAX_MARGIN, MAX_MARGIN + 1)
TOTALS = np.arange(0, MAX_TOTAL + 1)
_SQRT2 = math.sqrt(2.0)
_erf = np.frompyfunc(math.erf, 1, 1)


@dataclass(frozen=True)
class KeyNumbers:
    margin: tuple[float, ...]  # weight per |margin| 0..60 (0 = a tie: weight 0)
    total: tuple[float, ...]  # weight per total 0..160

    @classmethod
    def none(cls) -> "KeyNumbers":
        """No key numbers: the discretized normal, ties included (for comparisons)."""
        return cls((1.0,) * MARGIN_WEIGHTS, (1.0,) * (MAX_TOTAL + 1))

    def margin_table(self, mean: float, sigma: float) -> "Table":
        weights = np.asarray(self.margin)[np.minimum(np.abs(MARGINS), MARGIN_WEIGHTS - 1)]
        return Table(MARGINS, _normalize(_bins(MARGINS, mean, sigma) * weights))

    def total_table(self, mean: float, sigma: float) -> "Table":
        return Table(TOTALS, _normalize(_bins(TOTALS, mean, sigma) * np.asarray(self.total)))


@dataclass(frozen=True)
class Table:
    """A probability table over whole numbers."""

    values: NDArray[np.int64]
    probs: NDArray[np.float64]

    def p_over(self, line: float) -> float:
        return float(self.probs[self.values > line].sum())

    def p_push(self, line: float) -> float:
        if not float(line).is_integer():
            return 0.0
        return float(self.probs[self.values == int(line)].sum())

    def p_at(self, value: int) -> float:
        return self.p_push(value)


def two_way(table: Table, line: float) -> tuple[float, float, float]:
    """(P(over the line), P(under), P(push)); over = a home cover or the over."""
    over, push = table.p_over(line), table.p_push(line)
    return over, 1.0 - over - push, push


def _bins(values: NDArray[np.int64], mean: float, sigma: float) -> NDArray[np.float64]:
    edges = np.append(values - 0.5, values[-1] + 0.5)
    cdf = 0.5 * (1.0 + _erf((edges - mean) / (sigma * _SQRT2)).astype(float))
    return np.diff(cdf)


def _normalize(p: NDArray[np.float64]) -> NDArray[np.float64]:
    total = p.sum()
    return p / total if total > 0 else p


def as_weights(values: Sequence[float]) -> tuple[float, ...]:
    return tuple(float(v) for v in values)
