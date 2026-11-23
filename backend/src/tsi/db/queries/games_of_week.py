"""Stored games of the week (decision #141)."""

from collections.abc import Iterable
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tsi.db.models import Game, GameOfWeek
from tsi.db.queries.filters import one_of


def latest_poll_date(session: Session, through: date) -> date | None:
    """The newest poll week with picks, on or before `through`."""
    return session.scalar(
        select(func.max(GameOfWeek.poll_date)).where(GameOfWeek.poll_date <= through)
    )


def picks_for(session: Session, poll_date: date) -> list[GameOfWeek]:
    """That poll week's picks, FBS first, Power before Résumé."""
    query = (
        select(GameOfWeek)
        .where(GameOfWeek.poll_date == poll_date)
        .order_by(GameOfWeek.division, GameOfWeek.ranking_type)
    )
    return list(session.scalars(query))


def games_added_since(session: Session, game_ids: Iterable[int], since: datetime) -> set[int]:
    """Which of these games first appeared in the data after `since` (#157)."""
    ids = list(game_ids)
    if not ids:
        return set()
    query = select(Game.id).where(one_of(Game.id, ids), Game.created_at > since)
    return set(session.scalars(query))


def kickoffs(session: Session, game_ids: Iterable[int]) -> dict[int, datetime]:
    ids = list(game_ids)
    query = select(Game.id, Game.start_time).where(one_of(Game.id, ids))
    return {gid: start for gid, start in session.execute(query)} if ids else {}
