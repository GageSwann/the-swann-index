"""Conference membership and conference games of one season (for the season sim)."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from tsi.db.models import Game, TeamSeason
from tsi.db.queries.filters import one_of
from tsi.divisions import FCS, RATED_DIVISION


@dataclass(frozen=True)
class Member:
    team_id: int
    conference: str | None
    conference_division: str | None
    division: str = RATED_DIVISION  # fbs / fcs


@dataclass(frozen=True)
class ConferenceGameRow:
    id: int
    start_time: datetime | None
    home_id: int
    away_id: int
    home_points: int | None
    away_points: int | None
    completed: bool
    conference_game: bool
    notes: str | None

    @property
    def title_game(self) -> bool:
        """CFBD marks title games only in `notes` (not always as conference games). FCS
        playoff games ("FCS Championship - ...") are often filed as regular season."""
        notes = (self.notes or "").lower()
        return "championship" in notes and not is_fcs_playoff(notes)


def conference_members(
    session: Session, season: int, divisions: Sequence[str] = (RATED_DIVISION,)
) -> list[Member]:
    query = select(
        TeamSeason.team_id,
        TeamSeason.conference,
        TeamSeason.conference_division,
        TeamSeason.division,
    ).where(TeamSeason.season == season, one_of(TeamSeason.division, divisions))
    return [Member(*row) for row in session.execute(query)]


FCS_PLAYOFF_NOTE = "fcs championship"  # CFBD notes: "FCS Championship - First Round", ...


def is_fcs_playoff(notes: str | None) -> bool:
    return (notes or "").lower().startswith(FCS_PLAYOFF_NOTE)


def fcs_playoff_games(session: Session, season: int) -> set[int]:
    """Ids of the season's FCS playoff games (scheduled once the field is picked)."""
    query = select(Game.id).where(Game.season == season, Game.notes.ilike("FCS Championship%"))
    return set(session.scalars(query))


def moved_up_teams(session: Session, season: int, seasons: int) -> set[int]:
    """FCS teams in one of their first `seasons` FCS seasons after D-II/III (or below)."""
    rows = session.execute(
        select(TeamSeason.team_id, TeamSeason.season, TeamSeason.division).where(
            TeamSeason.season <= season
        )
    )
    first_fcs: dict[int, int] = {}
    lower: dict[int, list[int]] = {}
    for team, year, division in rows:
        if division == FCS:
            first_fcs[team] = min(first_fcs.get(team, year), year)
        elif division != RATED_DIVISION:
            lower.setdefault(team, []).append(year)
    return {
        t
        for t, first in first_fcs.items()
        if season - first < seasons and any(y < first for y in lower.get(t, ()))
    }


def conference_games(session: Session, season: int) -> list[ConferenceGameRow]:
    """Regular-season conference games plus anything billed as a championship."""
    query = select(
        Game.id,
        Game.start_time,
        Game.home_id,
        Game.away_id,
        Game.home_points,
        Game.away_points,
        Game.completed,
        Game.conference_game,
        Game.notes,
    ).where(
        Game.season == season,
        Game.season_type == "regular",
        or_(Game.conference_game, Game.notes.ilike("%championship%")),
    )
    return [ConferenceGameRow(*row) for row in session.execute(query)]
