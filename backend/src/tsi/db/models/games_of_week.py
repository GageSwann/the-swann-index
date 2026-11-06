"""Games of the week (Phase 13.4, decision #141): picked once per poll week, held all week.

One row per poll week (the Sunday, Eastern), division and ranking type. Written by the
first nightly run of the poll week; never updated (a new week gets new rows).
"""

from datetime import date, datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from tsi.db.base import Base, CreatedAtMixin


class GameOfWeek(CreatedAtMixin, Base):
    __tablename__ = "games_of_week"
    __table_args__ = (UniqueConstraint("poll_date", "division", "ranking_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    season: Mapped[int]
    poll_date: Mapped[date]  # the poll week's Sunday (Eastern)
    division: Mapped[str]  # fbs / fcs
    ranking_type: Mapped[str]  # power / resume
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    picked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    score: Mapped[float]
    quality: Mapped[float]  # 0..1: both teams' ranks
    closeness: Mapped[float]  # 0..1: TSI's win probability near 50%
    stakes: Mapped[float]  # 0..1: playoff and title odds riding on the result
    home_rank: Mapped[int | None]
    away_rank: Mapped[int | None]
    home_playoff_swing: Mapped[float | None]  # P(field | win) - P(field | loss)
    away_playoff_swing: Mapped[float | None]
    home_title_swing: Mapped[float | None]
    away_title_swing: Mapped[float | None]
