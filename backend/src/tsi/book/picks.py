"""TSI Plays: which edges become official picks, their ★ tier and stake (doc 05 §3-4).

A market's better side (book/edges.py) becomes a pick when its edge (shrunk
probability minus break-even, or minus the no-vig market probability for
moneylines) reaches the 1★ threshold; 2★ and 3★ need bigger edges. Moneyline
picks also need positive expected value at the market price.
Stakes are paper units: flat 1 unit, plus a suggested quarter-Kelly stake on a
100-unit bankroll, capped at 3 units.
"""

from dataclasses import dataclass

from tsi.book.edges import GameEdges, SideEdge
from tsi.book.odds import profit_per_unit

BANKROLL_UNITS = 100.0
KELLY_FRACTION = 0.25
MAX_KELLY_UNITS = 3.0
FLAT_UNITS = 1.0


@dataclass(frozen=True)
class PickRules:
    """Edge thresholds (probability points) for 1, 2 and 3 stars, per market."""

    spread: tuple[float, float, float] = (0.015, 0.03, 0.05)
    total: tuple[float, float, float] = (0.015, 0.03, 0.05)
    moneyline: tuple[float, float, float] = (0.03, 0.05, 0.08)


@dataclass(frozen=True)
class PickDecision:
    market: str  # 'spread' | 'total' | 'ml'
    side: str  # 'home' | 'away' | 'over' | 'under'
    line: float | None
    odds: int
    prob: float
    edge: float
    tier: int  # 1-3 stars
    stake_units: float  # flat
    kelly_units: float  # quarter Kelly, capped


def choose_picks(edges: GameEdges, rules: PickRules | None = None) -> list[PickDecision]:
    rules = rules or PickRules()
    candidates = [
        ("spread", edges.spread, rules.spread),
        ("total", edges.total, rules.total),
        ("ml", edges.moneyline, rules.moneyline),
    ]
    picks = []
    for market, side, thresholds in candidates:
        if side is None or (market == "ml" and side.ev <= 0):
            continue
        tier = star_tier(side.edge, thresholds)
        if tier:
            picks.append(_decision(market, side, tier))
    return picks


def star_tier(edge: float, thresholds: tuple[float, float, float]) -> int:
    """0 when below the 1★ threshold."""
    return sum(edge >= t for t in thresholds)


def kelly_units(prob: float, odds: int) -> float:
    """Quarter-Kelly stake in units of a 100-unit bankroll, capped (0 if no edge)."""
    b = profit_per_unit(odds)
    full = (b * prob - (1 - prob)) / b
    return min(MAX_KELLY_UNITS, max(0.0, KELLY_FRACTION * full * BANKROLL_UNITS))


def _decision(market: str, side: SideEdge, tier: int) -> PickDecision:
    return PickDecision(
        market=market,
        side=side.side,
        line=side.line,
        odds=side.odds,
        prob=side.prob,
        edge=side.edge,
        tier=tier,
        stake_units=FLAT_UNITS,
        kelly_units=round(kelly_units(side.prob, side.odds), 2),
    )
