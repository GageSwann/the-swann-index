"""Backtest the TSI Book (doc 05 §6): the picks it would have made, graded.

For every walk-forward game with an opening line: edges at the median opener
(the publish-time proxy) with the shrink learned on TRAIN, picks by the live
rules, graded on the final score, CLV against the closing consensus. Moneylines
are left out: history has no opening moneyline prices.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from tsi.backtest.walk_forward import Pick
from tsi.book.consensus import ConsensusLine
from tsi.book.edges import EdgeShrink, game_edges
from tsi.book.grading import clv_points, grade_pick
from tsi.book.picks import PickRules, choose_picks
from tsi.db.queries.market import OpeningLine
from tsi.model.distribution import DistributionParams


@dataclass(frozen=True)
class GradedBet:
    season: int
    market: str
    side: str
    tier: int
    result: str
    units: float  # flat 1 unit
    kelly_staked: float
    kelly_units: float
    clv: float | None  # points vs. the closing consensus, picked side's view


@dataclass(frozen=True)
class BookRecord:
    label: str
    market: str
    tier: int  # 0 = all tiers
    wins: int
    losses: int
    pushes: int
    units: float
    kelly_units: float
    kelly_staked: float
    clv: float | None  # mean points
    beat_close: float | None  # share of bets with CLV > 0

    @property
    def bets(self) -> int:
        return self.wins + self.losses + self.pushes

    @property
    def win_rate(self) -> float:
        decided = self.wins + self.losses
        return self.wins / decided if decided else 0.0

    @property
    def roi(self) -> float:
        return self.units / self.bets if self.bets else 0.0


def simulate_book(
    picks: Sequence[Pick],
    params: DistributionParams,
    shrink: EdgeShrink,
    opening: Mapping[int, OpeningLine],
    closing_spreads: Mapping[int, float],
    closing_totals: Mapping[int, float],
    rules: PickRules | None = None,
) -> list[GradedBet]:
    bets = []
    for p in picks:
        g, line = p.game, opening.get(p.game.id)
        if line is None:
            continue
        dist = params.for_game(p.predictive_margin, p.predictive_total)
        market = ConsensusLine(line.spread, line.total, None, None, None, 1)
        for d in choose_picks(game_edges(dist, market, shrink), rules):
            grade = grade_pick(d.market, d.side, d.line, d.odds, g.home_points, g.away_points)
            close = (closing_spreads if d.market == "spread" else closing_totals).get(g.id)
            bets.append(
                GradedBet(
                    season=g.season,
                    market=d.market,
                    side=d.side,
                    tier=d.tier,
                    result=grade.result,
                    units=grade.units_won,
                    kelly_staked=d.kelly_units,
                    kelly_units=grade.units_won * d.kelly_units,
                    clv=None if close is None else clv_points(d.market, d.side, d.line, close),
                )
            )
    return bets


def summarize_book(label: str, bets: Sequence[GradedBet]) -> list[BookRecord]:
    """One record per market (all tiers) and per market x tier."""
    groups: list[tuple[str, int, list[GradedBet]]] = []
    for market in sorted({b.market for b in bets}):
        in_market = [b for b in bets if b.market == market]
        groups.append((market, 0, in_market))
        groups += [(market, t, [b for b in in_market if b.tier == t]) for t in (1, 2, 3)]
    return [_record(label, market, tier, group) for market, tier, group in groups if group]


def _record(label: str, market: str, tier: int, bets: Sequence[GradedBet]) -> BookRecord:
    clvs = [b.clv for b in bets if b.clv is not None]
    return BookRecord(
        label=label,
        market=market,
        tier=tier,
        wins=sum(b.result == "win" for b in bets),
        losses=sum(b.result == "loss" for b in bets),
        pushes=sum(b.result == "push" for b in bets),
        units=sum(b.units for b in bets),
        kelly_units=sum(b.kelly_units for b in bets),
        kelly_staked=sum(b.kelly_staked for b in bets),
        clv=sum(clvs) / len(clvs) if clvs else None,
        beat_close=sum(c > 0 for c in clvs) / len(clvs) if clvs else None,
    )
