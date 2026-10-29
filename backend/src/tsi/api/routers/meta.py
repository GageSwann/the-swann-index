from fastapi import APIRouter

from tsi.api.deps import NowDep, SessionsDep, read
from tsi.services.read.meta import Meta, current_meta

router = APIRouter(tags=["meta"])


@router.get("/meta/current", response_model=Meta)
async def get_meta(
    sessions: SessionsDep,
    now: NowDep,
) -> Meta:
    """Current season and week, and when ratings and predictions were last updated."""
    return await read(sessions, lambda s: current_meta(s, now))
