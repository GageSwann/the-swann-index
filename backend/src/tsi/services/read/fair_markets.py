"""TSI's own prices for a game, without the TSI Book (decision #139).

The Book is owner-only, so public responses (the game center) carry TSI's
probabilities and fair (no-vig) odds per market and leave out the Book's vigged prices.
"""

from dataclasses import dataclass

from tsi.book.pricing import GameMarkets, Price, TwoWay


@dataclass(frozen=True)
class FairPrice:
    prob: float  # TSI probability this side wins at the line (given no push)
    fair: int  # American odds, no vig


@dataclass(frozen=True)
class FairTwoWay:
    line: float | None  # spread (home view) or total; None for the moneyline
    first: FairPrice  # home (spread, ML, team totals) or over (totals)
    second: FairPrice  # away or under
    push: float = 0.0  # P(push) at a whole-number line (key numbers, #118)


@dataclass(frozen=True)
class FairMarkets:
    fair_spread: float  # home view
    fair_total: float
    moneyline: FairTwoWay
    spread: FairTwoWay
    total: FairTwoWay
    home_total: FairTwoWay  # over / under on the home team's points
    away_total: FairTwoWay
    alt_spreads: list[FairTwoWay]
    alt_totals: list[FairTwoWay]


def fair_markets(m: GameMarkets) -> FairMarkets:
    return FairMarkets(
        fair_spread=m.fair_spread,
        fair_total=m.fair_total,
        moneyline=_two_way(m.moneyline),
        spread=_two_way(m.spread),
        total=_two_way(m.total),
        home_total=_two_way(m.home_total),
        away_total=_two_way(m.away_total),
        alt_spreads=[_two_way(t) for t in m.alt_spreads],
        alt_totals=[_two_way(t) for t in m.alt_totals],
    )


def _two_way(t: TwoWay) -> FairTwoWay:
    return FairTwoWay(t.line, _price(t.first), _price(t.second), t.push)


def _price(p: Price) -> FairPrice:
    return FairPrice(p.prob, p.fair)
