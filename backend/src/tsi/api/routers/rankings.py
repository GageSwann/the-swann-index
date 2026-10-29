from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from tsi.api.deps import NowDep, SessionsDep, read, season_or_current
from tsi.services.read.rankings import Rankings, RankingType, rankings

router = APIRouter(tags=["rankings"])


@router.get("/rankings", response_model=Rankings)
async def get_rankings(
    sessions: SessionsDep,
    now: NowDep,
    season: int | None = None,
    week: int | None = Query(None, description="Latest run within this week (default: latest)."),
    type: RankingType = "power",  # noqa: A002 (the documented query name)
    season_type: Literal["regular", "postseason"] | None = None,
) -> Rankings:
    """Power (how good now) or Résumé (what they've accomplished) rankings."""
    result = await read(
        sessions, lambda s: rankings(s, season_or_current(season, now), type, week, season_type)
    )
    if result is None:
        raise HTTPException(404, "No rankings for that season/week yet.")
    return result
