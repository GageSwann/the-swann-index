"""Games and per-team game stats."""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from tsi.db.base import Base, CreatedAtMixin


class Game(CreatedAtMixin, Base):
    __tablename__ = "games"
    __table_args__ = (
        CheckConstraint("home_id <> away_id", name="distinct_teams"),
        CheckConstraint("season_type IN ('regular', 'postseason')", name="season_type"),
        Index("ix_games_season_week", "season", "season_type", "week"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)  # CFBD id
    season: Mapped[int]
    week: Mapped[int]
    season_type: Mapped[str]
    start_time: Mapped[datetime | None]  # UTC; kickoff is the look-ahead cutoff
    home_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    away_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    venue_id: Mapped[int | None] = mapped_column(ForeignKey("venues.id"))
    neutral_site: Mapped[bool] = mapped_column(default=False)
    conference_game: Mapped[bool] = mapped_column(default=False)
    home_points: Mapped[int | None]
    away_points: Mapped[int | None]
    completed: Mapped[bool] = mapped_column(default=False)


class TeamGameStats(CreatedAtMixin, Base):
    """One row per team per game: that team's OFFENSE.

    A team's defensive numbers for a game are its opponent's offensive row,
    so nothing is stored twice.
    """

    __tablename__ = "team_game_stats"

    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    points: Mapped[int | None]
    plays: Mapped[int | None]
    drives: Mapped[int | None]
    yards: Mapped[int | None]
    epa_per_play: Mapped[float | None]
    rush_epa_per_play: Mapped[float | None]
    pass_epa_per_play: Mapped[float | None]
    success_rate: Mapped[float | None]
    explosiveness: Mapped[float | None]
    havoc_rate: Mapped[float | None]  # havoc allowed by this offense
    garbage_time_filtered: Mapped[bool] = mapped_column(default=True)
