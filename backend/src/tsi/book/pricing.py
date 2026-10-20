"""Price every market for one game from its score distribution (doc 05 §2).

Lines (home view for spreads, negative = home favored):
- fair spread / total: the distribution's means (where each side is exactly 50%)
- Book lines: the fair line rounded to the nearest half point, priced at the
  flat main-line odds (-110 by default); team totals the same way
- moneyline: win probability -> fair odds, plus `moneyline_hold`
- alt ladders: every `ladder_step` points around the main line, each side priced
  from its probability with `line_hold`
v1 is a continuous distribution, so whole-number lines carry no push probability;
key numbers (3, 7, ...) arrive with the v2 simulation.
"""

import math
from dataclasses import dataclass

from tsi.book.config import BookConfig
from tsi.book.odds import american_from_prob, vigged_american
from tsi.model.distribution import ScoreDistribution


@dataclass(frozen=True)
class Price:
    prob: float  # TSI probability this side wins at the line
    fair: int  # American odds, no vig
    book: int  # American odds the TSI Book offers


@dataclass(frozen=True)
class TwoWay:
    line: float | None  # spread (home view) or total; None for the moneyline
    first: Price  # home (spread, ML, team totals) or over (totals)
    second: Price  # away or under


@dataclass(frozen=True)
class GameMarkets:
    fair_spread: float  # home view
    fair_total: float
    moneyline: TwoWay
    spread: TwoWay
    total: TwoWay
    home_total: TwoWay  # over / under on the home team's points
    away_total: TwoWay
    alt_spreads: list[TwoWay]
    alt_totals: list[TwoWay]


def price_game(dist: ScoreDistribution, config: BookConfig | None = None) -> GameMarkets:
    c = config or BookConfig()
    spread_line = round_half(-dist.margin)
    total_line = round_half(dist.total)
    win = dist.home_win_prob
    return GameMarkets(
        fair_spread=-dist.margin,
        fair_total=dist.total,
        moneyline=TwoWay(None, _price(win, c.moneyline_hold), _price(1 - win, c.moneyline_hold)),
        spread=_main(spread_line, _cover(dist, spread_line), c),
        total=_main(total_line, dist.p_total_over(total_line), c),
        home_total=_team_total(dist.home_points, dist.p_home_over, c),
        away_total=_team_total(dist.away_points, dist.p_away_over, c),
        alt_spreads=[
            _two_way(line, _cover(dist, line), c.line_hold) for line in _ladder(spread_line, c)
        ],
        alt_totals=[
            _two_way(line, dist.p_total_over(line), c.line_hold) for line in _ladder(total_line, c)
        ],
    )


def round_half(x: float) -> float:
    """Nearest half point; quarter points round up (Python's round() would bank-round)."""
    return math.floor(x * 2 + 0.5) / 2


def _cover(dist: ScoreDistribution, spread: float) -> float:
    """P(home covers `spread`), home view: home margin + spread > 0."""
    return dist.p_margin_over(-spread)


def _team_total(mean: float, p_over, c: BookConfig) -> TwoWay:
    line = round_half(mean)
    return _main(line, p_over(line), c)


def _main(line: float, p_first: float, c: BookConfig) -> TwoWay:
    if c.main_line_odds is None:
        return _two_way(line, p_first, c.line_hold)
    return TwoWay(
        line,
        Price(p_first, american_from_prob(p_first), c.main_line_odds),
        Price(1 - p_first, american_from_prob(1 - p_first), c.main_line_odds),
    )


def _two_way(line: float | None, p_first: float, hold: float) -> TwoWay:
    return TwoWay(line, _price(p_first, hold), _price(1 - p_first, hold))


def _price(p: float, hold: float) -> Price:
    return Price(p, american_from_prob(p), vigged_american(p, hold))


def _ladder(main: float, c: BookConfig) -> list[float]:
    steps = int(c.ladder_width / c.ladder_step)
    return [main + i * c.ladder_step for i in range(-steps, steps + 1)]
