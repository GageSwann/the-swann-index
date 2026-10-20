"""Closing market lines, averaged across providers (a simple consensus for comparisons)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tsi.db.models import Game, MarketLine


def closing_spreads(session: Session, through_season: int) -> dict[int, float]:
    """game_id -> mean closing spread (home view, negative = home favored)."""
    return _closing_mean(session, MarketLine.spread, through_season)


def closing_totals(session: Session, through_season: int) -> dict[int, float]:
    """game_id -> mean closing over/under total (points)."""
    return _closing_mean(session, MarketLine.total, through_season)


def _closing_mean(session: Session, column, through_season: int) -> dict[int, float]:
    query = (
        select(MarketLine.game_id, func.avg(column))
        .join(Game, Game.id == MarketLine.game_id)
        .where(MarketLine.is_closing, column.is_not(None), Game.season <= through_season)
        .group_by(MarketLine.game_id)
    )
    return {game_id: float(value) for game_id, value in session.execute(query)}
