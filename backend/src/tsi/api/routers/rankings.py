from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from tsi.api.deps import get_now, get_session, season_or_current
from tsi.services.read.rankings import Rankings, RankingType, rankings

router = APIRouter(tags=["rankings"])


@router.get("/rankings", response_model=Rankings)
def get_rankings(
    session: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
    season: int | None = None,
    week: int | None = Query(None, description="Latest run within this week (default: latest)."),
    type: RankingType = "power",  # noqa: A002 (the documented query name)
    season_type: Literal["regular", "postseason"] | None = None,
) -> Rankings:
    """Power (how good now) or Résumé (what they've accomplished) rankings."""
    result = rankings(session, season_or_current(season, now), type, week, season_type)
    if result is None:
        raise HTTPException(404, "No rankings for that season/week yet.")
    return result
