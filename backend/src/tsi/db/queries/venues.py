"""Where games are played: the venue a game card shows under its kickoff (#209)."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import Game, Venue
from tsi.db.queries.filters import one_of


@dataclass(frozen=True)
class GameVenue:
    name: str  # "Rice-Eccles Stadium"
    city: str | None
    state: str | None  # empty or None abroad ("Aviva Stadium", Dublin)


def game_venues(session: Session, game_ids: list[int]) -> dict[int, GameVenue]:
    """Game id -> its venue, for the games that have one (one small join, a row per game)."""
    if not game_ids:
        return {}
    query = (
        select(Game.id, Venue.name, Venue.city, Venue.state)
        .join(Venue, Venue.id == Game.venue_id)
        .where(one_of(Game.id, game_ids))
    )
    return {gid: GameVenue(name, city, state) for gid, name, city, state in session.execute(query)}
