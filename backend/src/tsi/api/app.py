"""FastAPI application factory. Run locally with `tsi serve`."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from tsi import __version__
from tsi.api.routers import book, games, matchup, meta, model, rankings, teams
from tsi.config import Settings, get_settings
from tsi.db.engine import make_engine, make_session_factory


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = make_engine(settings or get_settings())
        app.state.sessions = make_session_factory(engine)
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(
        title="The Swann Index API",
        version=__version__,
        description="Read-only college football ratings, predictions and TSI Book data.",
        lifespan=lifespan,
    )
    for router in (meta, rankings, teams, games, book, model, matchup):
        app.include_router(router.router)
    return app
