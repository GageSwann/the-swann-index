"""TSI vs. the market: probabilities shrunk toward the line, and edges (doc 05 §3, decision #52).

The market is more accurate than TSI, so TSI's raw probabilities at a market line
are overconfident. The Book instead moves only a fraction k of the way from the
market's number to TSI's:
    shrunk mean = line_mean + k * (TSI mean - line_mean)
    P(home covers spread s) = Phi(k * (TSI margin + s) / sigma_margin)
    P(over total t)         = Phi(k * (TSI total - t) / sigma_total)
    P(home wins)            = Phi((-s + k * (TSI margin + s)) / sigma_margin)
k is learned per market on past games against the line the Book bets
(`book/shrink_fit.py`). The market sizes the edge; it never changes TSI's own
projection.
Edges: spread/total = P(side) - break-even at -110; moneyline = P(win) - market
no-vig probability, plus expected value per unit at the market price.
"""

import math
from dataclasses import dataclass

from tsi.book.consensus import ConsensusLine
from tsi.book.odds import prob_from_american, profit_per_unit
from tsi.model.distribution import ScoreDistribution

STANDARD_ODDS = -110  # assumed price on spreads/totals (CFBD lines carry no spread odds)
BREAK_EVEN = prob_from_american(STANDARD_ODDS)  # 0.5238


@dataclass(frozen=True)
class EdgeShrink:
    k_spread: float  # also used for the moneyline (same margin distribution)
    k_total: float


@dataclass(frozen=True)
class SideEdge:
    side: str  # 'home'/'away' (spread, ml) or 'over'/'under' (total)
    line: float | None  # home-view spread or total; None for the moneyline
    odds: int
    prob: float  # shrunk probability this side wins
    edge: float  # prob - break-even (spread/total) or prob - market no-vig (ml)
    ev: float  # expected units won per unit staked


@dataclass(frozen=True)
class GameEdges:
    spread_diff: float | None  # TSI spread - market spread (points, home view)
    total_diff: float | None
    spread: SideEdge | None  # the better side of each market, None without a line
    total: SideEdge | None
    moneyline: SideEdge | None


def game_edges(dist: ScoreDistribution, market: ConsensusLine, shrink: EdgeShrink) -> GameEdges:
    spread = total = ml = None
    if market.spread is not None:
        p_home = cover_prob(dist, market.spread, shrink.k_spread)
        spread = _best(("home", p_home), ("away", 1 - p_home), market.spread)
        if market.home_ml is not None and market.away_ml is not None and market.home_prob:
            ml = _moneyline(dist, market, shrink.k_spread)
    if market.total is not None:
        p_over = over_prob(dist, market.total, shrink.k_total)
        total = _best(("over", p_over), ("under", 1 - p_over), market.total)
    return GameEdges(
        spread_diff=None if market.spread is None else -dist.margin - market.spread,
        total_diff=None if market.total is None else dist.total - market.total,
        spread=spread,
        total=total,
        moneyline=ml,
    )


def cover_prob(dist: ScoreDistribution, spread: float, k: float) -> float:
    """Shrunk P(home covers `spread`), home view."""
    return _phi(k * (dist.margin + spread) / dist.sigma_margin)


def over_prob(dist: ScoreDistribution, total: float, k: float) -> float:
    return _phi(k * (dist.total - total) / dist.sigma_total)


def _moneyline(dist: ScoreDistribution, market: ConsensusLine, k: float) -> SideEdge:
    line_margin = -market.spread
    p_home = _phi((line_margin + k * (dist.margin - line_margin)) / dist.sigma_margin)
    sides = [
        ("home", p_home, market.home_ml, market.home_prob),
        ("away", 1 - p_home, market.away_ml, 1 - market.home_prob),
    ]
    edges = [SideEdge(side, None, odds, p, p - fair, _ev(p, odds)) for side, p, odds, fair in sides]
    return max(edges, key=lambda e: e.ev)


def _best(first: tuple[str, float], second: tuple[str, float], line: float) -> SideEdge:
    side, p = max(first, second, key=lambda s: s[1])
    return SideEdge(side, line, STANDARD_ODDS, p, p - BREAK_EVEN, _ev(p, STANDARD_ODDS))


def _ev(p: float, odds: int) -> float:
    return p * profit_per_unit(odds) - (1 - p)


def _phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
