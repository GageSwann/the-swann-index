"""Against-the-spread record vs. the closing line (doc 01 target: > 50%; 52.4% breaks even at -110).

The model "bets" the side it likes more than the market: home if its margin is
above the market margin, away if below. Pushes and exact agreement are skipped.
"""

from collections.abc import Sequence
from dataclasses import dataclass

BREAK_EVEN = 0.5238  # win rate needed at -110


@dataclass(frozen=True)
class AtsRecord:
    min_edge: float  # only games where |model - market| >= this many points
    wins: int
    losses: int
    pushes: int

    @property
    def bets(self) -> int:
        return self.wins + self.losses

    @property
    def win_rate(self) -> float:
        return self.wins / self.bets if self.bets else 0.0


def ats_record(
    model_margin: Sequence[float],
    market_margin: Sequence[float],
    actual_margin: Sequence[float],
    min_edge: float = 0.0,
) -> AtsRecord:
    wins = losses = pushes = 0
    for model, market, actual in zip(model_margin, market_margin, actual_margin, strict=True):
        edge = model - market
        if edge == 0 or abs(edge) < min_edge:
            continue
        result = actual - market  # > 0: home covered
        if result == 0:
            pushes += 1
        elif (result > 0) == (edge > 0):
            wins += 1
        else:
            losses += 1
    return AtsRecord(min_edge, wins, losses, pushes)
