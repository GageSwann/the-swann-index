from fastapi import APIRouter, HTTPException

from tsi.api.deps import NowDep, SessionsDep, read, season_or_current
from tsi.db.queries.team_info import TeamRef
from tsi.services.read.teams import TeamProfile, team_list, team_profile

router = APIRouter(tags=["teams"])


@router.get("/teams", response_model=list[TeamRef])
async def get_teams(
    sessions: SessionsDep,
    now: NowDep,
    season: int | None = None,
) -> list[TeamRef]:
    """FBS teams of a season (slug, name, colors, logo, conference)."""
    return await read(sessions, lambda s: team_list(s, season_or_current(season, now)))


@router.get("/teams/{slug}", response_model=TeamProfile)
async def get_team(
    slug: str,
    sessions: SessionsDep,
    now: NowDep,
    season: int | None = None,
) -> TeamProfile:
    """Team profile: ratings and ranks, rating history, schedule with results and TSI odds."""
    profile = await read(
        sessions, lambda s: team_profile(s, slug, season_or_current(season, now), now)
    )
    if profile is None:
        raise HTTPException(404, f"Unknown team {slug!r}.")
    return profile
