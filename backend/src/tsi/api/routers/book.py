from fastapi import APIRouter, Depends

from tsi.api.deps import NowDep, SessionsDep, read, require_owner, season_or_current
from tsi.services.read.ledger import Ledger, ledger

# Owner-only (decision #139): left out of the public API spec, 404 without the key.
router = APIRouter(tags=["book"], include_in_schema=False, dependencies=[Depends(require_owner)])


@router.get("/book/ledger", response_model=Ledger)
async def get_ledger(
    sessions: SessionsDep,
    now: NowDep,
    season: int | None = None,
) -> Ledger:
    """TSI Book picks for a season with record, units, ROI and closing line value."""
    return await read(sessions, lambda s: ledger(s, season_or_current(season, now), now))
