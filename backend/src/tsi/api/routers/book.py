from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tsi.api.deps import get_now, get_session, season_or_current
from tsi.services.read.ledger import Ledger, ledger

router = APIRouter(tags=["book"])


@router.get("/book/ledger", response_model=Ledger)
def get_ledger(
    session: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
    season: int | None = None,
) -> Ledger:
    """TSI Book picks for a season with record, units, ROI and closing line value."""
    return ledger(session, season_or_current(season, now), now)
