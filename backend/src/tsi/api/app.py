"""FastAPI application factory. Run locally with `tsi serve`."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from tsi import __version__
from tsi.api.caching import CachingMiddleware
from tsi.api.routers import book, games, matchup, meta, model, rankings, teams
from tsi.config import Settings, get_settings
from tsi.db.engine import make_engine, make_session_factory


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = make_engine(settings)
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
    # Added innermost first: caching sees the uncompressed JSON (ETag), gzip compresses
    # it, and CORS (outermost) answers preflight requests before anything else runs.
    app.add_middleware(CachingMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.tsi_cors_origins,
        allow_methods=["GET"],
        allow_headers=["If-None-Match"],
        expose_headers=["ETag"],
        max_age=86400,
    )
    return app
