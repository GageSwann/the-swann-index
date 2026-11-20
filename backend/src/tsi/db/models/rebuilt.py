"""Rebuilt forecasts (roadmap 13.8, decision #152): what TSI would have said before a game
the nightly job never published, replayed later through the same live code.

Kept apart from `predictions` on purpose (rule 2, #57): a rebuilt forecast was computed
after kickoff, so it is never a published snapshot, never has picks and is never graded.
One per game and variant: the forecast from the last replayed day before kickoff (`as_of`,
that day's nightly cutoff). The API shows it, marked rebuilt, only for games without any
published snapshot. Columns mirror `predictions` so the same views can show it.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from tsi.db.base import Base, CreatedAtMixin
from tsi.db.models.ratings import VARIANT_CHECK


class RebuiltForecast(CreatedAtMixin, Base):
    __tablename__ = "rebuilt_forecasts"
    __table_args__ = (
        CheckConstraint(VARIANT_CHECK, name="variant"),
        CheckConstraint("home_win_prob BETWEEN 0 AND 1", name="win_prob_range"),
    )

    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), primary_key=True)
    variant: Mapped[str] = mapped_column(primary_key=True, default="raw")
    # The rebuilt rating run of that day; None when the day already had a real run.
    run_id: Mapped[int | None] = mapped_column(ForeignKey("model_runs.id"))
    as_of: Mapped[datetime]  # the replayed cutoff: data from games before it only
    proj_home: Mapped[float]
    proj_away: Mapped[float]
    spread: Mapped[float]  # fair, home view, negative = home favored
    total: Mapped[float]
    home_win_prob: Mapped[float]
    sigma_margin: Mapped[float]
    sigma_total: Mapped[float]
    rho: Mapped[float]
    fair_home_ml: Mapped[int]
    fair_away_ml: Mapped[int]
    # The Book's prices are kept so rows match `predictions` column for column; the
    # public API never shows Book prices (#139) and rebuilt rows never get picks.
    book_home_ml: Mapped[int]
    book_away_ml: Mapped[int]
    book_spread_home_odds: Mapped[int]
    book_spread_away_odds: Mapped[int]
    book_over_odds: Mapped[int]
    book_under_odds: Mapped[int]
    adjustment_ids: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
