from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from tsi.api.deps import get_now, get_session
from tsi.services.read.matchup import Matchup, UnknownTeamError, matchup

router = APIRouter(tags=["matchup"])


@router.get("/matchup", response_model=Matchup)
def get_matchup(
    home: str,
    away: str,
    session: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
    neutral: bool = False,
) -> Matchup:
    """Hypothetical game between any two teams (slugs), predicted as of now."""
    if home == away:
        raise HTTPException(400, "Pick two different teams.")
    try:
        return matchup(session, home, away, neutral, now)
    except UnknownTeamError as exc:
        raise HTTPException(404, f"Unknown team: {exc}.") from exc
