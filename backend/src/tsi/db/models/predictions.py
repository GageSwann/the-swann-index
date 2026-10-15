"""Published prediction snapshots and the paper-trading picks graded against them.

`predictions` is INSERT-ONLY (rule 2); the migration adds a trigger that rejects
UPDATE/DELETE. The locked snapshot for a game is derived, not flagged: the latest
row with `published_at < games.start_time`.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from tsi.db.base import Base, CreatedAtMixin
from tsi.db.models.ratings import VARIANT_CHECK


class Prediction(CreatedAtMixin, Base):
    __tablename__ = "predictions"
    __table_args__ = (
        CheckConstraint(VARIANT_CHECK, name="variant"),
        CheckConstraint("home_win_prob BETWEEN 0 AND 1", name="win_prob_range"),
        Index("ix_predictions_lookup", "game_id", "variant", "published_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("model_runs.id"), index=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    variant: Mapped[str] = mapped_column(default="raw")
    published_at: Mapped[datetime]
    # Score distribution (bivariate normal v1); alt ladders are derived from these.
    proj_home: Mapped[float]
    proj_away: Mapped[float]
    spread: Mapped[float]  # home view, negative = home favored
    total: Mapped[float]
    home_win_prob: Mapped[float]
    sigma_margin: Mapped[float]
    sigma_total: Mapped[float]
    rho: Mapped[float]
    # Fair (no-vig) and TSI Book (vigged) prices, American odds.
    fair_home_ml: Mapped[int]
    fair_away_ml: Mapped[int]
    book_home_ml: Mapped[int]
    book_away_ml: Mapped[int]
    book_spread_home_odds: Mapped[int]
    book_spread_away_odds: Mapped[int]
    book_over_odds: Mapped[int]
    book_under_odds: Mapped[int]


class Pick(CreatedAtMixin, Base):
    """A paper bet. Grading fields are filled after the game; the prediction never changes."""

    __tablename__ = "picks"
    __table_args__ = (
        UniqueConstraint("prediction_id", "market"),
        CheckConstraint("market IN ('spread', 'total', 'ml')", name="market"),
        CheckConstraint("side IN ('home', 'away', 'over', 'under')", name="side"),
        CheckConstraint("tier BETWEEN 1 AND 3", name="tier"),
        CheckConstraint("result IN ('win', 'loss', 'push')", name="result"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"))
    market: Mapped[str]
    side: Mapped[str]
    line_taken: Mapped[float | None]  # None for moneyline
    odds_taken: Mapped[int]
    edge: Mapped[float]
    tier: Mapped[int]
    stake_units: Mapped[float]  # flat
    kelly_units: Mapped[float | None]  # 1/4 Kelly, capped
    closing_line: Mapped[float | None]
    closing_odds: Mapped[int | None]
    result: Mapped[str | None]
    units_won: Mapped[float | None]
    graded_at: Mapped[datetime | None]
