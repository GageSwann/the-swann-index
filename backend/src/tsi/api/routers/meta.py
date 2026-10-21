from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tsi.api.deps import get_now, get_session
from tsi.services.read.meta import Meta, current_meta

router = APIRouter(tags=["meta"])


@router.get("/meta/current", response_model=Meta)
def meta_current(
    session: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
) -> Meta:
    """Current season and week, and when ratings and predictions were last updated."""
    return current_meta(session, now)
