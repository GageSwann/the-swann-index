"""Stored games of the week (decision #141)."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tsi.db.models import GameOfWeek


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
