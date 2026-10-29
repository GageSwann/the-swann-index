from fastapi import APIRouter, HTTPException

from tsi.api.deps import NowDep, SessionsDep, read, season_or_current
from tsi.services.read.playoff import Playoff, playoff

router = APIRouter(tags=["playoff"])


@router.get("/playoff", response_model=Playoff)
async def get_playoff(
    sessions: SessionsDep,
    now: NowDep,
    season: int | None = None,
) -> Playoff:
    """Playoff odds, fair futures odds and a projected bracket (regular season only)."""
    result = await read(sessions, lambda s: playoff(s, season_or_current(season, now)))
    if result is None:
        raise HTTPException(404, "No playoff projection for that season yet.")
    return result
