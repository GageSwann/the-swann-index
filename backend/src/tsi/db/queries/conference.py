"""Conference membership and conference games of one season (for the season sim)."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from tsi.db.models import Game, TeamSeason
from tsi.divisions import RATED_DIVISION


@dataclass(frozen=True)
class Member:
    team_id: int
    conference: str | None
    conference_division: str | None


@dataclass(frozen=True)
class ConferenceGameRow:
    id: int
    start_time: datetime | None
    home_id: int
    away_id: int
    home_points: int | None
    away_points: int | None
    completed: bool
    conference_game: bool
    notes: str | None

    @property
    def title_game(self) -> bool:
        """CFBD marks title games only in `notes` (not always as conference games)."""
        return "championship" in (self.notes or "").lower()


def conference_members(session: Session, season: int) -> list[Member]:
    query = select(TeamSeason.team_id, TeamSeason.conference, TeamSeason.conference_division).where(
        TeamSeason.season == season, TeamSeason.division == RATED_DIVISION
    )
    return [Member(*row) for row in session.execute(query)]


def conference_games(session: Session, season: int) -> list[ConferenceGameRow]:
    """Regular-season conference games plus anything billed as a championship."""
    query = select(
        Game.id,
        Game.start_time,
        Game.home_id,
        Game.away_id,
        Game.home_points,
        Game.away_points,
        Game.completed,
        Game.conference_game,
        Game.notes,
    ).where(
        Game.season == season,
        Game.season_type == "regular",
        or_(Game.conference_game, Game.notes.ilike("%championship%")),
    )
    return [ConferenceGameRow(*row) for row in session.execute(query)]
