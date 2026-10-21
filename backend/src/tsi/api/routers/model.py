from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tsi.api.deps import get_now, get_session, season_or_current
from tsi.services.read.report import ModelReport, model_report

router = APIRouter(tags=["model"])


@router.get("/model/report", response_model=ModelReport)
def get_model_report(
    session: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
    season: int | None = None,
) -> ModelReport:
    """Backtest headline metrics plus this season's live accuracy of published predictions."""
    return model_report(session, season_or_current(season, now), now)
