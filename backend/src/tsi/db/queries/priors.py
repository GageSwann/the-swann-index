"""Preseason prior inputs and per-season FBS membership."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import Prior, TeamSeason
from tsi.divisions import RATED_DIVISION

PriorKey = tuple[int, int]  # (season, team_id)


@dataclass(frozen=True)
class PriorRow:
    talent: float | None = None
    returning: float | None = None
    returning_passing: float | None = None
    recruiting: float | None = None
    portal: float | None = None
    new_coach: bool | None = None


def prior_inputs(session: Session, first_season: int, last_season: int) -> dict[PriorKey, PriorRow]:
    query = select(
        Prior.season,
        Prior.team_id,
        Prior.talent,
        Prior.returning_ppa,
        Prior.returning_passing_ppa,
        Prior.recruiting_points,
        Prior.portal_net,
        Prior.new_head_coach,
    ).where(Prior.season.between(first_season, last_season))
    return {(row[0], row[1]): PriorRow(*row[2:]) for row in session.execute(query)}


def fbs_teams(session: Session, first_season: int, last_season: int) -> dict[int, set[int]]:
    """season -> FBS team ids that season."""
    return division_teams(session, first_season, last_season, RATED_DIVISION)


def division_teams(
    session: Session, first_season: int, last_season: int, division: str
) -> dict[int, set[int]]:
    """season -> ids of the teams in `division` that season."""
    query = select(TeamSeason.season, TeamSeason.team_id).where(
        TeamSeason.division == division,
        TeamSeason.season.between(first_season, last_season),
    )
    teams: dict[int, set[int]] = {}
    for season, team_id in session.execute(query):
        teams.setdefault(season, set()).add(team_id)
    return teams
