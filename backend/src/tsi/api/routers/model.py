from fastapi import APIRouter, Depends

from tsi.api.deps import NowDep, SessionsDep, read, require_owner, season_or_current
from tsi.services.read.report import ModelReport, model_report

# Owner-only (decision #139): left out of the public API spec, 404 without the key.
router = APIRouter(tags=["model"], include_in_schema=False, dependencies=[Depends(require_owner)])


@router.get("/model/report", response_model=ModelReport)
async def get_model_report(
    sessions: SessionsDep,
    now: NowDep,
    season: int | None = None,
) -> ModelReport:
    """Backtest headline metrics plus this season's live accuracy of published predictions."""
    return await read(sessions, lambda s: model_report(s, season_or_current(season, now), now))
