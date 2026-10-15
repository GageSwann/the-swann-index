"""Teams, per-season membership, and venues.

Conference and division live on `team_seasons`, never on `teams`: membership
changes by year (realignment, FCS->FBS moves), and backtests must see each
season as it was. Division is free text (fbs, fcs, ii, iii, ...), so no
division is hard-coded into the schema.
"""

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from tsi.db.base import Base, CreatedAtMixin


class Venue(CreatedAtMixin, Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)  # CFBD id
    name: Mapped[str]
    city: Mapped[str | None]
    state: Mapped[str | None]
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    elevation_m: Mapped[float | None]
    dome: Mapped[bool | None]


class Team(CreatedAtMixin, Base):
    """Stable team identity only."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)  # CFBD id
    school: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True)
    mascot: Mapped[str | None]
    abbreviation: Mapped[str | None]
    color: Mapped[str | None]
    alt_color: Mapped[str | None]
    logo_url: Mapped[str | None]
    venue_id: Mapped[int | None] = mapped_column(ForeignKey("venues.id"))


class TeamSeason(CreatedAtMixin, Base):
    __tablename__ = "team_seasons"
    __table_args__ = (Index("ix_team_seasons_season_division", "season", "division"),)

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    season: Mapped[int] = mapped_column(primary_key=True)
    conference: Mapped[str | None]
    division: Mapped[str]
