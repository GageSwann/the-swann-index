"""Closing market lines, averaged across providers (a simple consensus for comparisons)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tsi.db.models import Game, MarketLine


def closing_spreads(session: Session, through_season: int) -> dict[int, float]:
    """game_id -> mean closing spread (home view, negative = home favored)."""
    query = (
        select(MarketLine.game_id, func.avg(MarketLine.spread))
        .join(Game, Game.id == MarketLine.game_id)
        .where(MarketLine.is_closing, MarketLine.spread.is_not(None), Game.season <= through_season)
        .group_by(MarketLine.game_id)
    )
    return {game_id: float(spread) for game_id, spread in session.execute(query)}
