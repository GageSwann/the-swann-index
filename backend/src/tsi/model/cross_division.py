"""FBS-vs-FCS margin scale (Phase 11, decision #124).

The stacks learn from FBS-vs-FBS games only (#109), and on FBS-vs-FCS games their
margins overshoot: out of sample the FBS team was favored by about 30% too much
(+5.5 to +9.4 points a season, 2022-25), most of all in a team's first two games,
when the prediction leans on priors and Elo. The fix scales those games' margins
toward zero, with one factor for early games (stage bucket <= EARLY_BUCKET) and one
for the rest, least squares through the origin on held-out predictions. Their game
totals ran low (+1.9 to +5.1 points a season), so they also get a points offset.

Applies only when one team is FBS and the other an individually rated FCS team
(model/ratings/design.rated_id); pooled lower divisions are left alone. Pure.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from tsi.divisions import RATED_DIVISION, is_individual_fcs

EARLY_BUCKET = 1  # stage buckets 0-1: either team has played fewer than two games
MIN_GAMES = 30  # fewer fitted games in a group: leave that group unscaled


@dataclass(frozen=True)
class CrossDivision:
    early: float = 1.0  # margin factors
    late: float = 1.0
    total: float = 0.0  # points added to the game total

    def scale(self, bucket: int) -> float:
        return self.early if bucket <= EARLY_BUCKET else self.late


NONE = CrossDivision()


def is_cross_division(home_div: str, away_div: str, season: int) -> bool:
    """One FBS team against an individually rated FCS team."""
    divs = (home_div, away_div)
    if divs.count(RATED_DIVISION) != 1:
        return False
    other = away_div if home_div == RATED_DIVISION else home_div
    return is_individual_fcs(other, season)


@dataclass(frozen=True)
class CrossGame:
    bucket: int  # stage bucket
    margin: float  # predicted
    actual_margin: float
    total: float  # predicted
    actual_total: float


def fit_cross_division(games: Sequence[CrossGame]) -> CrossDivision:
    """Fit on held-out FBS-vs-FCS predictions."""

    def factor(group: list[tuple[float, float]]) -> float:
        if len(group) < MIN_GAMES:
            return 1.0
        xx = sum(p * p for p, _ in group)
        return sum(p * a for p, a in group) / xx if xx else 1.0

    early = [(g.margin, g.actual_margin) for g in games if g.bucket <= EARLY_BUCKET]
    late = [(g.margin, g.actual_margin) for g in games if g.bucket > EARLY_BUCKET]
    total = 0.0
    if len(games) >= MIN_GAMES:
        total = sum(g.actual_total - g.total for g in games) / len(games)
    return CrossDivision(factor(early), factor(late), total)
