"""Preseason prior inputs and per-season FBS membership."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import Prior, TeamSeason

PriorKey = tuple[int, int]  # (season, team_id)


def prior_inputs(
    session: Session, first_season: int, last_season: int
) -> dict[PriorKey, tuple[float | None, float | None]]:
    """(season, team_id) -> (talent, returning_ppa)."""
    query = select(Prior.season, Prior.team_id, Prior.talent, Prior.returning_ppa).where(
        Prior.season.between(first_season, last_season)
    )
    return {(s, t): (talent, ret) for s, t, talent, ret in session.execute(query)}


def fbs_teams(session: Session, first_season: int, last_season: int) -> dict[int, set[int]]:
    """season -> FBS team ids that season."""
    query = select(TeamSeason.season, TeamSeason.team_id).where(
        TeamSeason.division == "fbs", TeamSeason.season.between(first_season, last_season)
    )
    teams: dict[int, set[int]] = {}
    for season, team_id in session.execute(query):
        teams.setdefault(season, set()).add(team_id)
    return teams
