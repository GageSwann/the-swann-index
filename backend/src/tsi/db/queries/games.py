"""Game rows for read pages: a week's games, a team's schedule, one game."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from tsi.db.models import Game


@dataclass(frozen=True)
class GameRow:
    id: int
    season: int
    week: int
    season_type: str
    start_time: datetime | None
    start_time_tbd: bool
    home_id: int
    away_id: int
    neutral: bool
    conference_game: bool
    completed: bool
    home_points: int | None
    away_points: int | None
    notes: str | None


COLUMNS = (
    Game.id,
    Game.season,
    Game.week,
    Game.season_type,
    Game.start_time,
    Game.start_time_tbd,
    Game.home_id,
    Game.away_id,
    Game.neutral_site,
    Game.conference_game,
    Game.completed,
    Game.home_points,
    Game.away_points,
    Game.notes,
)


def week_games(session: Session, season: int, week: int, season_type: str) -> list[GameRow]:
    query = (
        select(*COLUMNS)
        .where(Game.season == season, Game.week == week, Game.season_type == season_type)
        .order_by(Game.start_time, Game.id)
    )
    return [GameRow(*row) for row in session.execute(query)]


def team_games(session: Session, season: int, team_id: int) -> list[GameRow]:
    query = (
        select(*COLUMNS)
        .where(Game.season == season, or_(Game.home_id == team_id, Game.away_id == team_id))
        .order_by(Game.start_time, Game.id)
    )
    return [GameRow(*row) for row in session.execute(query)]


def season_games(session: Session, season: int, game_ids: list[int]) -> list[GameRow]:
    query = select(*COLUMNS).where(Game.season == season, Game.id.in_(game_ids))
    return [GameRow(*row) for row in session.execute(query)]


def game_by_id(session: Session, game_id: int) -> GameRow | None:
    row = session.execute(select(*COLUMNS).where(Game.id == game_id)).first()
    return GameRow(*row) if row else None
