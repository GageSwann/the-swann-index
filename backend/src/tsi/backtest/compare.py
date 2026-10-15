"""Compare two sets of team ratings (e.g. TSI final vs. SP+ final): agreement statistics."""

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Agreement:
    teams: int
    pearson: float  # linear agreement of the ratings
    spearman: float  # agreement of the orderings (rank correlation)
    biggest_gaps: list[tuple[int, float, float]]  # (team, ours, theirs), largest |rank gap| first


def _ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(-values)
    ranks = np.empty(len(values))
    ranks[order] = np.arange(1, len(values) + 1)
    return ranks


def compare_ratings(
    ours: Mapping[int, float], theirs: Mapping[int, float], top_gaps: int = 5
) -> Agreement:
    teams = sorted(set(ours) & set(theirs))
    a = np.array([ours[t] for t in teams])
    b = np.array([theirs[t] for t in teams])
    rank_a, rank_b = _ranks(a), _ranks(b)
    gaps = sorted(range(len(teams)), key=lambda i: -abs(rank_a[i] - rank_b[i]))[:top_gaps]
    return Agreement(
        teams=len(teams),
        pearson=float(np.corrcoef(a, b)[0, 1]),
        spearman=float(np.corrcoef(rank_a, rank_b)[0, 1]),
        biggest_gaps=[(teams[i], float(a[i]), float(b[i])) for i in gaps],
    )
