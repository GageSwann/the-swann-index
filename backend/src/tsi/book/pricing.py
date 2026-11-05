"""Price every market for one game from its score distribution (doc 05 §2).

Lines (home view for spreads, negative = home favored):
- fair spread / total: the distribution's means (where each side is exactly 50%)
- Book lines: the fair line rounded to the nearest half point, priced at the
  flat main-line odds (-110 by default); team totals the same way
- moneyline: win probability -> fair odds, plus `moneyline_hold`
- alt ladders: every `ladder_step` points around the main line, each side priced
  from its probability with `line_hold`
With key numbers (decision #118; `model/key_numbers.py`), spreads, totals and the alt
ladders come from whole-number tables: a whole-number line has a push probability, and
each side's probability (and price) is conditional on no push. Moneylines and team
totals stay on the smooth distribution (the tables leave win probability unchanged).
"""

import math
from dataclasses import dataclass

from tsi.book.config import BookConfig
from tsi.book.odds import american_from_prob, vigged_american
from tsi.model.distribution import ScoreDistribution
from tsi.model.key_numbers import KeyNumbers, Table, two_way


@dataclass(frozen=True)
class Price:
    prob: float  # TSI probability this side wins at the line
    fair: int  # American odds, no vig
    book: int  # American odds the TSI Book offers


@dataclass(frozen=True)
class TwoWay:
    line: float | None  # spread (home view) or total; None for the moneyline
    first: Price  # home (spread, ML, team totals) or over (totals); prob given no push
    second: Price  # away or under
    push: float = 0.0  # P(push) at a whole-number line (key numbers, #118)


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


def price_game(
    dist: ScoreDistribution, config: BookConfig | None = None, keys: KeyNumbers | None = None
) -> GameMarkets:
    """`keys`: the artifact's key-number weights; None = the smooth distribution only."""
    c = config or BookConfig()
    spread_line = round_half(-dist.margin)
    total_line = round_half(dist.total)
    win = dist.home_win_prob
    cover, over = _markets(dist, keys)
    return GameMarkets(
        fair_spread=-dist.margin,
        fair_total=dist.total,
        moneyline=TwoWay(None, _price(win, c.moneyline_hold), _price(1 - win, c.moneyline_hold)),
        spread=_main(spread_line, cover(spread_line), c),
        total=_main(total_line, over(total_line), c),
        home_total=_team_total(dist.home_points, dist.p_home_over, c),
        away_total=_team_total(dist.away_points, dist.p_away_over, c),
        alt_spreads=[_two_way(line, cover(line), c.line_hold) for line in _ladder(spread_line, c)],
        alt_totals=[_two_way(line, over(line), c.line_hold) for line in _ladder(total_line, c)],
    )


Chances = tuple[float, float]  # (P(first side wins | no push), P(push))


def _markets(dist: ScoreDistribution, keys: KeyNumbers | None):
    """line -> chances, for spreads (home covers) and totals (over)."""
    if keys is None:
        return (lambda s: (_cover(dist, s), 0.0)), (lambda t: (dist.p_total_over(t), 0.0))
    margins = keys.margin_table(dist.margin, dist.sigma_margin)
    totals = keys.total_table(dist.total, dist.sigma_total)
    return (lambda s: _no_push(margins, -s)), (lambda t: _no_push(totals, t))


def _no_push(table: Table, line: float) -> Chances:
    first, second, push = two_way(table, line)
    decided = first + second
    return (first / decided if decided > 0 else 0.5), push


def round_half(x: float) -> float:
    """Nearest half point; quarter points round up (Python's round() would bank-round)."""
    return math.floor(x * 2 + 0.5) / 2


def _cover(dist: ScoreDistribution, spread: float) -> float:
    """P(home covers `spread`), home view: home margin + spread > 0."""
    return dist.p_margin_over(-spread)


def _team_total(mean: float, p_over, c: BookConfig) -> TwoWay:
    line = round_half(mean)
    return _main(line, (p_over(line), 0.0), c)


def _main(line: float, chances: Chances, c: BookConfig) -> TwoWay:
    p_first, push = chances
    if c.main_line_odds is None:
        return _two_way(line, chances, c.line_hold)
    return TwoWay(
        line,
        Price(p_first, american_from_prob(p_first), c.main_line_odds),
        Price(1 - p_first, american_from_prob(1 - p_first), c.main_line_odds),
        push,
    )


def _two_way(line: float | None, chances: Chances, hold: float) -> TwoWay:
    p_first, push = chances
    return TwoWay(line, _price(p_first, hold), _price(1 - p_first, hold), push)


def _price(p: float, hold: float) -> Price:
    return Price(p, american_from_prob(p), vigged_american(p, hold))


def _ladder(main: float, c: BookConfig) -> list[float]:
    steps = int(c.ladder_width / c.ladder_step)
    return [main + i * c.ladder_step for i in range(-steps, steps + 1)]
