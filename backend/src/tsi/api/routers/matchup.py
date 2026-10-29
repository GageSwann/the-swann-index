from fastapi import APIRouter, HTTPException

from tsi.api.deps import NowDep, SessionsDep, read
from tsi.services.read.matchup import Matchup, UnknownTeamError, matchup

router = APIRouter(tags=["matchup"])


@router.get("/matchup", response_model=Matchup)
async def get_matchup(
    home: str,
    away: str,
    sessions: SessionsDep,
    now: NowDep,
    neutral: bool = False,
) -> Matchup:
    """Hypothetical game between any two teams (slugs), predicted as of now."""
    if home == away:
        raise HTTPException(400, "Pick two different teams.")
    try:
        return await read(sessions, lambda s: matchup(s, home, away, neutral, now))
    except UnknownTeamError as exc:
        raise HTTPException(404, f"Unknown team: {exc}.") from exc
