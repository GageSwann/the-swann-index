"""Preseason prior (doc 04 §3): predict a team's offense and defense before any games.

    prior_side = d + a * last_season_side + sum(b_k * input_k)

Inputs: last season's final FBS rating (that side), talent composite, returning
production (overall and passing), 4-year recruiting average, net transfer portal,
and a new-head-coach flag.

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

FEATURES = (
    "last",
    "talent",
    "returning",
    "returning_passing",
    "recruiting",
    "portal",
    "new_coach",
)
SIDES = ("off", "defense")
MIN_SAMPLES = 20  # don't fit a subset model on fewer teams than this


@dataclass(frozen=True)
class PriorInputs:
    last: TeamRating | None  # last season's final FBS rating
    talent: float | None = None
    returning: float | None = None
    returning_passing: float | None = None
    recruiting: float | None = None
    portal: float | None = None
    new_coach: bool | None = None

    def values(self, side: str) -> dict[str, float | None]:
        last = getattr(self.last, side) if self.last is not None else None
        coach = None if self.new_coach is None else float(self.new_coach)
        return {
            "last": last,
            "talent": self.talent,
            "returning": self.returning,
            "returning_passing": self.returning_passing,
            "recruiting": self.recruiting,
            "portal": self.portal,
            "new_coach": coach,
        }


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
        # One matrix per side (NaN = missing input); each subset model selects its rows.
        values = np.array(
            [
                [np.nan if v is None else v for v in inputs.values(side).values()]
                for inputs, _ in samples
            ],
            dtype=float,
        ).reshape(len(samples), len(FEATURES))
        targets = np.array([getattr(final, side) for _, final in samples], dtype=float)
        for subset in _subsets_largest_first(FEATURES):
            cols = [FEATURES.index(f) for f in subset]
            usable = ~np.isnan(values[:, cols]).any(axis=1)
            if usable.sum() < MIN_SAMPLES:
                continue
            x = np.column_stack([np.ones(usable.sum()), values[usable][:, cols]])
            coefs[(side, subset)] = np.linalg.lstsq(x, targets[usable], rcond=None)[0]
    return PriorModel(coefs)


def _subsets_largest_first(features: Iterable[str]) -> list[tuple[str, ...]]:
    items = tuple(features)
    return [c for size in range(len(items), -1, -1) for c in combinations(items, size)]
