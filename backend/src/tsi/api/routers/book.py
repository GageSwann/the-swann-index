from fastapi import APIRouter

from tsi.api.deps import NowDep, SessionsDep, read, season_or_current
from tsi.services.read.ledger import Ledger, ledger

router = APIRouter(tags=["book"])


@router.get("/book/ledger", response_model=Ledger)
async def get_ledger(
    sessions: SessionsDep,
    now: NowDep,
    season: int | None = None,
) -> Ledger:
    """TSI Book picks for a season with record, units, ROI and closing line value."""
    return await read(sessions, lambda s: ledger(s, season_or_current(season, now), now))
