"""Request dependencies: database reads, and "now" (both overridable in tests).

Endpoints are `async` and run their database work through `read()`: it opens a session in
a worker thread, runs the read, and closes the session (returning its connection to the
pool) before the thread is released. FastAPI then serializes the response on the event
loop. With sync endpoints and a yield-dependency session, a finished request kept its
connection until after serialization, which waited for a free thread; under a burst (a
site build) every thread could be waiting for a connection, a deadlock broken only by the
pool's 30 s timeout (500s, decision #102).
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool

from tsi.ingest.freshness import current_season


async def get_sessions(request: Request) -> sessionmaker[Session]:
    return request.app.state.sessions


async def get_now() -> datetime:
    return datetime.now(UTC)


SessionsDep = Annotated[sessionmaker[Session], Depends(get_sessions)]
NowDep = Annotated[datetime, Depends(get_now)]


async def read[T](sessions: sessionmaker[Session], fn: Callable[[Session], T]) -> T:
    """Run `fn` with its own session in a worker thread; the connection is back in the
    pool before the thread is."""

    def work() -> T:
        with sessions() as session:
            return fn(session)

    return await run_in_threadpool(work)


def season_or_current(season: int | None, now: datetime) -> int:
    return season if season is not None else current_season(now)
