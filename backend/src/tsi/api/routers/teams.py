from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from tsi.api.deps import get_now, get_session, season_or_current
from tsi.db.queries.team_info import TeamRef
from tsi.services.read.teams import TeamProfile, team_list, team_profile

router = APIRouter(tags=["teams"])


@router.get("/teams", response_model=list[TeamRef])
def get_teams(
    session: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
    season: int | None = None,
) -> list[TeamRef]:
    """FBS teams of a season (slug, name, colors, logo, conference)."""
    return team_list(session, season_or_current(season, now))


@router.get("/teams/{slug}", response_model=TeamProfile)
def get_team(
    slug: str,
    session: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
    season: int | None = None,
) -> TeamProfile:
    """Team profile: ratings and ranks, rating history, schedule with results and TSI odds."""
    profile = team_profile(session, slug, season_or_current(season, now), now)
    if profile is None:
        raise HTTPException(404, f"Unknown team {slug!r}.")
    return profile
