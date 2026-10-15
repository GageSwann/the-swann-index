"""Preseason priors, model runs, and team ratings."""

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from tsi.db.base import Base, CreatedAtMixin

VARIANT_CHECK = "variant IN ('raw', 'adjusted')"


class Prior(CreatedAtMixin, Base):
    __tablename__ = "priors"

    season: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    last_season_rating: Mapped[float | None]
    returning_ppa: Mapped[float | None]
    talent: Mapped[float | None]
    prior_rating: Mapped[float | None]


class ModelRun(CreatedAtMixin, Base):
    """One execution of the model: a live weekly run or a backtest step."""

    __tablename__ = "model_runs"
    __table_args__ = (
        CheckConstraint("kind IN ('live', 'backtest')", name="kind"),
        Index("ix_model_runs_season_week", "season", "season_type", "week"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str]
    season: Mapped[int]
    week: Mapped[int]
    season_type: Mapped[str]
    run_at: Mapped[datetime]
    model_version: Mapped[str]  # tsi-v{major}.{minor}
    params: Mapped[dict[str, Any]]
    git_sha: Mapped[str | None]


class TeamRating(CreatedAtMixin, Base):
    """Ratings in points vs. an average team. `raw` = pure stats; `adjusted` adds manual tweaks."""

    __tablename__ = "team_ratings"
    __table_args__ = (CheckConstraint(VARIANT_CHECK, name="variant"),)

    run_id: Mapped[int] = mapped_column(ForeignKey("model_runs.id"), primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    variant: Mapped[str] = mapped_column(primary_key=True, default="raw")
    rating: Mapped[float]
    off_rating: Mapped[float]
    def_rating: Mapped[float]
    pace: Mapped[float | None]
    rank_power: Mapped[int | None]
    sor: Mapped[float | None]
    rank_resume: Mapped[int | None]
