"""The official FCS bracket on `/playoff` (#157): the real field by position and the real
playoff games, each with its score once final or TSI's published win chance before."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from tsi.db.queries.playoff_games import (
    BracketMismatchError,
    fcs_playoff_schedule,
    official_field,
)
from tsi.db.queries.snapshots import current_snapshots
from tsi.services.read.common import current_snapshot
from tsi.sim.fcs_brackets import FCS_BRACKETS


@dataclass(frozen=True)
class PlayoffGameView:
    """A scheduled or played playoff game; the site matches it to a bracket game by its
    two teams."""

    game_id: int
    start_time: datetime
    home_team_id: int
    away_team_id: int
    home_points: int | None
    away_points: int | None
    completed: bool
    home_win_prob: float | None  # TSI's shown forecast (locked once it kicked off)


def official_fcs_field(session: Session, season: int) -> list[int] | None:
    """The official field's team ids by position, if this season has one."""
    bracket = FCS_BRACKETS.get(season)
    if bracket is None:
        return None
    try:
        return official_field(session, bracket.field)
    except BracketMismatchError:
        return None


def fcs_playoff_games(session: Session, season: int, now: datetime) -> list[PlayoffGameView]:
    games = fcs_playoff_schedule(session, season)
    snaps = current_snapshots(session, [g.id for g in games], now)
    out = []
    for g in games:
        snap, _ = current_snapshot(snaps.get(g.id, []), g.start_time, now)
        out.append(
            PlayoffGameView(
                game_id=g.id,
                start_time=g.start_time,
                home_team_id=g.home_id,
                away_team_id=g.away_id,
                home_points=g.home_points,
                away_points=g.away_points,
                completed=g.completed,
                home_win_prob=snap.home_win_prob if snap else None,
            )
        )
    return out
