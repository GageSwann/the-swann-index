"""Predictive margin (backlog B1, decision #37): a learned blend of every pre-kickoff signal.

    margin = sum_k beta[b, k] * feature_k        b = season-stage bucket

Features (home view):
    site     1 home / 0 neutral
    ppd      opponent-adjusted points-per-drive margin (points)
    success  opponent-adjusted success-rate margin (successful plays)
    prior    preseason prior rating difference (points)
    elo      Elo margin (points; carries information from earlier seasons)
The bucket is the fewer games played by the two teams. Early buckets learn to lean
on the prior and Elo; late buckets lean on this season's stats, so the prior's fade
is learned rather than hand-set. EPA was tested and dropped (redundant with success
rate and PPD; it produced unstable negative weights).
Fit: ridge least squares per bucket, no intercept (the problem is symmetric), with
`site` unpenalized.
"""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

FEATURES = ("site", "ppd", "success", "prior", "elo")
UNPENALIZED = ("site",)
BUCKET_EDGES = (0, 1, 2, 3, 4, 6, 9)  # bucket i covers edges[i] <= games < edges[i + 1]
DEFAULT_LAM = 1000.0


def stage_bucket(min_games_played: int) -> int:
    return max(i for i, edge in enumerate(BUCKET_EDGES) if min_games_played >= edge)


@dataclass(frozen=True)
class StackSample:
    bucket: int
    features: tuple[float, ...]  # in FEATURES order
    margin: float  # actual home-view margin (target)


@dataclass(frozen=True)
class StackModel:
    coefs: dict[int, np.ndarray]

    def predict(self, bucket: int, features: Sequence[float]) -> float:
        coef = self.coefs.get(bucket)
        if coef is None:  # unseen stage: borrow the nearest fitted bucket
            coef = self.coefs[min(self.coefs, key=lambda b: abs(b - bucket))]
        return float(np.dot(coef, features))


def fit_stack(samples: Sequence[StackSample], lam: float = DEFAULT_LAM) -> StackModel:
    penalty = np.array([0.0 if f in UNPENALIZED else lam for f in FEATURES]) + 1e-9
    by_bucket: dict[int, list[StackSample]] = defaultdict(list)
    for s in samples:
        by_bucket[s.bucket].append(s)
    coefs = {}
    for bucket, group in by_bucket.items():
        x = np.array([s.features for s in group], dtype=float)
        y = np.array([s.margin for s in group], dtype=float)
        coefs[bucket] = np.linalg.solve(x.T @ x + np.diag(penalty), x.T @ y)
    return StackModel(coefs)
