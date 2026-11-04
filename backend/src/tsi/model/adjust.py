"""Apply manual adjustments to a game's forecast (doc 04 §11, decisions #103, #104).

Each adjustment moves a team's offense (points it scores) and defense (points it keeps
off the board), per game:

    home points += home.off - away.def
    away points += away.off - home.def

so the margin moves by (home.off + home.def) - (away.off + away.def) and the total by
(home.off + away.off) - (home.def + away.def). The adjusted distribution is rebuilt
from the shifted means with the model's own spread parameters, so it is priced exactly
like a raw one. Pure: no I/O.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from tsi.model.distribution import DistributionParams, ScoreDistribution


class AdjustmentLike(Protocol):
    id: int
    team_id: int
    off_points: float
    def_points: float

    def covers(self, kickoff: datetime) -> bool: ...


@dataclass(frozen=True)
class GameAdjustment:
    ids: tuple[int, ...]  # the adjustments applied, oldest first
    home_off: float = 0.0
    home_def: float = 0.0
    away_off: float = 0.0
    away_def: float = 0.0

    @property
    def margin_shift(self) -> float:
        return (self.home_off + self.home_def) - (self.away_off + self.away_def)

    @property
    def total_shift(self) -> float:
        return (self.home_off + self.away_off) - (self.home_def + self.away_def)


def game_adjustment(
    home_id: int, away_id: int, kickoff: datetime, adjustments: Iterable[AdjustmentLike]
) -> GameAdjustment | None:
    """The adjustments covering this game, summed per side; None when there are none."""
    applied = [a for a in adjustments if a.team_id in (home_id, away_id) and a.covers(kickoff)]
    if not applied:
        return None

    def total(team_id: int, field: str) -> float:
        return sum(getattr(a, field) for a in applied if a.team_id == team_id)

    return GameAdjustment(
        ids=tuple(sorted(a.id for a in applied)),
        home_off=total(home_id, "off_points"),
        home_def=total(home_id, "def_points"),
        away_off=total(away_id, "off_points"),
        away_def=total(away_id, "def_points"),
    )


def adjust_distribution(
    raw: ScoreDistribution, adjustment: GameAdjustment, params: DistributionParams
) -> ScoreDistribution:
    return params.for_game(raw.margin + adjustment.margin_shift, raw.total + adjustment.total_shift)
