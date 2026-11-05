"""Lopsided-game totals and the underdog floor (Phase 12.3, model v1.7, decision #132).

Projected scores are (total +- margin) / 2, and the totals stack doesn't know that a
lopsided game still leaves the underdog some points: the bigger the predicted margin,
the more the total ran low (2015-25 walk-forward: about +5 to +8 points past a 42-point
margin), and FBS-vs-FCS mismatches projected negative underdog scores (43 in the
backtest, as low as -13.9). Two pieces, both pure:

- `bump`: total += slope * max(0, |margin| - THRESHOLD), only in games with an
  individually rated FCS team (`applies`), slope learned by least squares on held-out
  predictions of those games (THRESHOLD chosen on 2015-22). Bumping FBS-vs-FBS totals
  too fit totals no better there and cost the Book (validation ROI 14.0% -> 6.7%,
  CLV +0.93 -> +0.76), so those keep their totals.
- `floored_total`: a hard rule, applied wherever a score distribution is built: the
  underdog is never projected below MIN_POINTS, so no path (model, manual adjustments,
  hypothetical matchups, any game kind) can produce a negative or zero projected score.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from tsi.divisions import is_individual_fcs

THRESHOLD = 20.0  # points of predicted margin before the total starts to grow
MIN_POINTS = 1.0  # the underdog's projected points never go below this
MIN_GAMES = 30  # fewer fitted games: no bump


@dataclass(frozen=True)
class Lopsided:
    slope: float = 0.0  # total points added per point of |margin| past THRESHOLD

    def bump(self, margin: float, total: float) -> float:
        return total + self.slope * max(0.0, abs(margin) - THRESHOLD)


NONE = Lopsided()


def applies(home_div: str, away_div: str, season: int) -> bool:
    """The bump is for games with an individually rated FCS team (FBS-vs-FCS, FCS-vs-FCS)."""
    return is_individual_fcs(home_div, season) or is_individual_fcs(away_div, season)


def floored_total(margin: float, total: float) -> float:
    """The total, raised if needed so the underdog's projected points >= MIN_POINTS."""
    return max(total, abs(margin) + 2 * MIN_POINTS)


@dataclass(frozen=True)
class TotalGame:
    margin: float  # predicted
    total: float  # predicted
    actual_total: float


def fit_lopsided(games: Sequence[TotalGame]) -> Lopsided:
    """Least squares through the origin of (actual - predicted total) on the hinge."""
    hinge = [(max(0.0, abs(g.margin) - THRESHOLD), g.actual_total - g.total) for g in games]
    hh = sum(h * h for h, _ in hinge)
    if len(games) < MIN_GAMES or not hh:
        return NONE
    return Lopsided(sum(h * r for h, r in hinge) / hh)
