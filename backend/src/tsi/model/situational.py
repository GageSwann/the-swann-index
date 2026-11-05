"""Rest, byes and short weeks (Phase 11, decision #120).

A small global adjustment to the predicted margin, added after the stack (rest effects
don't depend on the stage of the season, and per-bucket ridge shrank a 0/1 bye flag to
nothing). Features, home view (+ favors home), from each team's days since its previous
game this season (None for its first game):

    rest   clip(home rest - away rest, -7, 7) days (0 if either is unknown)
    bye    [home had 13+ days] - [away had 13+ days]
    short  [home had <= 5.5 days] - [away had <= 5.5 days]

Coefficients are least squares with a light ridge on the stack's held-out errors (TRAIN
in the backtest, every season in production). Screened alternatives (travel distance,
time zones, altitude, team-specific home field) did not help out of sample. Pure.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

import numpy as np

FEATURES = ("rest", "bye", "short")
BYE_DAYS = 13.0
SHORT_DAYS = 5.5
MAX_REST_GAP = 7.0
LAM = 50.0


@dataclass(frozen=True)
class Situational:
    coefs: tuple[float, ...]  # FEATURES order; zeros = no adjustment

    def shift(self, features: Sequence[float]) -> float:
        return float(np.dot(self.coefs, features))


NONE = Situational((0.0,) * len(FEATURES))


def rest_days(kickoffs: Sequence[datetime], kickoff: datetime) -> float | None:
    """Days since the team's previous game this season (`kickoffs` sorted); None if first."""
    before = [t for t in kickoffs if t < kickoff]
    return None if not before else (kickoff - before[-1]).total_seconds() / 86400


def features(home_rest: float | None, away_rest: float | None) -> tuple[float, float, float]:
    gap = 0.0
    if home_rest is not None and away_rest is not None:
        gap = float(np.clip(home_rest - away_rest, -MAX_REST_GAP, MAX_REST_GAP))

    def flag(rest: float | None, test) -> float:
        return float(rest is not None and test(rest))

    bye = flag(home_rest, lambda r: r >= BYE_DAYS) - flag(away_rest, lambda r: r >= BYE_DAYS)
    short = flag(home_rest, lambda r: r <= SHORT_DAYS) - flag(away_rest, lambda r: r <= SHORT_DAYS)
    return gap, bye, short


def fit_situational(rows: Sequence[tuple[Sequence[float], float]], lam: float = LAM) -> Situational:
    """`rows`: (features, residual = actual margin - stacked prediction)."""
    if not rows:
        return NONE
    x = np.array([f for f, _ in rows], dtype=float)
    y = np.array([r for _, r in rows], dtype=float)
    coef = np.linalg.solve(x.T @ x + lam * np.eye(x.shape[1]), x.T @ y)
    return Situational(tuple(float(c) for c in coef))
