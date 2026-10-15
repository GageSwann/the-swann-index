"""Sportsbook market lines (from CFBD /lines, later other providers)."""

from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from tsi.db.base import Base, CreatedAtMixin


class MarketLine(CreatedAtMixin, Base):
    """A provider's line for a game at fetch time.

    Sign convention: `spread` is from the HOME team's view (negative = home favored).
    """

    __tablename__ = "market_lines"
    __table_args__ = (UniqueConstraint("game_id", "provider", "fetched_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), index=True)
    provider: Mapped[str]
    spread: Mapped[float | None]
    spread_open: Mapped[float | None]
    total: Mapped[float | None]
    total_open: Mapped[float | None]
    home_ml: Mapped[int | None]
    away_ml: Mapped[int | None]
    fetched_at: Mapped[datetime]
    is_closing: Mapped[bool] = mapped_column(default=False)
