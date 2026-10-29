from fastapi import APIRouter

from tsi.api.deps import NowDep, SessionsDep, read, season_or_current
from tsi.services.read.report import ModelReport, model_report

router = APIRouter(tags=["model"])


@router.get("/model/report", response_model=ModelReport)
async def get_model_report(
    sessions: SessionsDep,
    now: NowDep,
    season: int | None = None,
) -> ModelReport:
    """Backtest headline metrics plus this season's live accuracy of published predictions."""
    return await read(sessions, lambda s: model_report(s, season_or_current(season, now), now))
