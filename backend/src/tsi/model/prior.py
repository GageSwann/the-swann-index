"""Preseason prior (doc 04 §3): predict a team's offense and defense before any games.

    prior_side = a * last_season_side + b * talent + c * returning_production + d

Fit by least squares on past seasons (target: that season's final `season`
rating). Inputs can be missing (no talent before 2015, no returning production
for teams new to FBS, no previous FBS rating), so a separate model is fit for
every subset of inputs, and each team uses the model matching what it has.
Least squares naturally regresses the prior toward the mean.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from itertools import combinations

import numpy as np

from tsi.model.ratings.fit import TeamRating

FEATURES = ("last", "talent", "returning")
SIDES = ("off", "defense")
MIN_SAMPLES = 20  # don't fit a subset model on fewer teams than this


@dataclass(frozen=True)
class PriorInputs:
    last: TeamRating | None  # last season's final FBS rating
    talent: float | None
    returning: float | None

    def values(self, side: str) -> dict[str, float | None]:
        last = getattr(self.last, side) if self.last is not None else None
        return {"last": last, "talent": self.talent, "returning": self.returning}


ModelKey = tuple[str, tuple[str, ...]]  # (side, available features)


@dataclass(frozen=True)
class PriorModel:
    coefs: dict[ModelKey, np.ndarray]  # [intercept, *feature coefficients]

    def predict(self, inputs: PriorInputs) -> TeamRating:
        return TeamRating(*(self._predict_side(inputs, side) for side in SIDES))

    def _predict_side(self, inputs: PriorInputs, side: str) -> float:
        values = inputs.values(side)
        available = tuple(f for f in FEATURES if values[f] is not None)
        for subset in _subsets_largest_first(available):
            coef = self.coefs.get((side, subset))
            if coef is not None:
                return float(
                    coef[0] + sum(c * values[f] for c, f in zip(coef[1:], subset, strict=True))
                )
        return 0.0  # nothing usable: an average team


def fit_prior_model(samples: Sequence[tuple[PriorInputs, TeamRating]]) -> PriorModel:
    """`samples`: (preseason inputs, that season's final rating) per team-season."""
    coefs: dict[ModelKey, np.ndarray] = {}
    for side in SIDES:
        for subset in _subsets_largest_first(FEATURES):
            usable = [
                (inputs.values(side), getattr(final, side))
                for inputs, final in samples
                if all(inputs.values(side)[f] is not None for f in subset)
            ]
            if len(usable) < MIN_SAMPLES:
                continue
            x = np.array([[1.0, *(v[f] for f in subset)] for v, _ in usable])
            y = np.array([target for _, target in usable])
            coefs[(side, subset)] = np.linalg.lstsq(x, y, rcond=None)[0]
    return PriorModel(coefs)


def _subsets_largest_first(features: Iterable[str]) -> list[tuple[str, ...]]:
    items = tuple(features)
    return [c for size in range(len(items), -1, -1) for c in combinations(items, size)]
