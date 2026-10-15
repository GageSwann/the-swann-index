"""Win-probability calibration: predicted vs. observed in probability bins (doc 05 §8).

Uses the favorite's perspective (p >= 0.5), so 5 bins from 50% to 100% each hold
enough games. Target: every bin within ±3 percentage points.
"""

from collections.abc import Sequence
from dataclasses import dataclass

TOLERANCE = 0.03


@dataclass(frozen=True)
class CalibrationBin:
    low: float
    high: float
    games: int
    predicted: float  # mean predicted win prob of the favorite
    observed: float  # share of those favorites that won

    @property
    def error(self) -> float:
        return self.observed - self.predicted

    @property
    def within_tolerance(self) -> bool:
        return abs(self.error) <= TOLERANCE


def calibration_table(
    probs: Sequence[float],
    outcomes: Sequence[float],
    edges: Sequence[float] = (0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
) -> list[CalibrationBin]:
    """`probs`: P(home wins); `outcomes`: 1 home won, 0 lost, 0.5 tie."""
    fav = [(p, o) if p >= 0.5 else (1 - p, 1 - o) for p, o in zip(probs, outcomes, strict=True)]
    bins = []
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        inside = [(p, o) for p, o in fav if low <= p < high or (high == 1.0 and p == 1.0)]
        if inside:
            bins.append(
                CalibrationBin(
                    low,
                    high,
                    len(inside),
                    sum(p for p, _ in inside) / len(inside),
                    sum(o for _, o in inside) / len(inside),
                )
            )
    return bins
