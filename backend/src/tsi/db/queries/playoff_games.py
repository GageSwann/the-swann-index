"""A season's FCS playoff games as scheduled and played (#157): CFBD files them with notes
"FCS Championship - First Round", ... (often as regular-season games)."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import Game
from tsi.db.queries.team_info import team_ids_by_slug


@dataclass(frozen=True)
class PlayoffGame:
    id: int
    start_time: datetime
    home_id: int
    away_id: int
    neutral: bool
    home_points: int | None
    away_points: int | None
    completed: bool
    notes: str | None

    @property
    def winner(self) -> int | None:
        """The winning team, once the game is final (playoff games can't end tied)."""
        if not self.completed or self.home_points is None or self.away_points is None:
            return None
        if self.home_points == self.away_points:
            return None
        return self.home_id if self.home_points > self.away_points else self.away_id

    @property
    def first_round(self) -> bool:
        return "first round" in (self.notes or "").lower()


def fcs_playoff_schedule(session: Session, season: int) -> list[PlayoffGame]:
    """Every FCS playoff game of the season so far, by kickoff."""
    query = (
        select(
            Game.id,
            Game.start_time,
            Game.home_id,
            Game.away_id,
            Game.neutral_site,
            Game.home_points,
            Game.away_points,
            Game.completed,
            Game.notes,
        )
        .where(Game.season == season, Game.notes.ilike("FCS Championship%"))
        .order_by(Game.start_time, Game.id)
    )
    return [PlayoffGame(*row) for row in session.execute(query)]


class BracketMismatchError(ValueError):
    """The entered bracket doesn't agree with the data (unknown team, other first round)."""


def official_field(session: Session, slugs: Sequence[str]) -> list[int]:
    """A bracket's team ids by position, from its team slugs."""
    ids = team_ids_by_slug(session, slugs)
    missing = [s for s in slugs if s not in ids]
    if missing:
        raise BracketMismatchError(f"unknown teams in the bracket: {missing}")
    return [ids[s] for s in slugs]
