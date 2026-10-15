"""Season calendar: week boundaries per season type (from CFBD /calendar)."""

from datetime import datetime

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from tsi.db.base import Base, CreatedAtMixin


class CalendarWeek(CreatedAtMixin, Base):
    __tablename__ = "calendar_weeks"
    __table_args__ = (
        CheckConstraint("season_type IN ('regular', 'postseason')", name="season_type"),
    )

    season: Mapped[int] = mapped_column(primary_key=True)
    season_type: Mapped[str] = mapped_column(primary_key=True)
    week: Mapped[int] = mapped_column(primary_key=True)
    start_date: Mapped[datetime]  # UTC
    end_date: Mapped[datetime]  # UTC
