from typing import Literal

from fastapi import APIRouter, HTTPException

from tsi.api.deps import NowDep, SessionsDep, read, season_or_current
from tsi.services.read.playoff import Playoff, playoff

router = APIRouter(tags=["playoff"])


@router.get("/playoff", response_model=Playoff)
async def get_playoff(
    sessions: SessionsDep,
    now: NowDep,
    season: int | None = None,
    division: Literal["fbs", "fcs"] = "fbs",
) -> Playoff:
    """Playoff odds, fair futures odds and a projected bracket (regular season only):
    the College Football Playoff (`fbs`) or the 24-team FCS playoff (`fcs`)."""
    result = await read(sessions, lambda s: playoff(s, season_or_current(season, now), division))
    if result is None:
        raise HTTPException(404, "No playoff projection for that season yet.")
    return result
