"""FastAPI application factory. Run locally with `tsi serve`; export the spec with `tsi openapi`."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from tsi import __version__
from tsi.api.caching import CachingMiddleware
from tsi.api.routers import book, games, health, matchup, meta, model, rankings, teams
from tsi.config import Settings, get_settings
from tsi.db.engine import make_engine, make_session_factory

TITLE = "The Swann Index API"
DESCRIPTION = "Read-only college football ratings, predictions and TSI Book data."


def create_app(settings: Settings | None = None) -> FastAPI:
    """The served app: settings (database, CORS origins) are resolved now."""
    settings = settings or get_settings()
    return build_app(settings.tsi_cors_origins, settings)


def build_app(cors_origins: list[str], settings: Settings | None = None) -> FastAPI:
    """App without reading settings until it starts (so the spec can be built anywhere)."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = make_engine(settings or get_settings())
        app.state.sessions = make_session_factory(engine)
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(
        title=TITLE,
        version=__version__,
        description=DESCRIPTION,
        lifespan=lifespan,
        # Operation ids = the router function names (get_rankings, ...): clean TS client names.
        generate_unique_id_function=lambda route: route.name,
    )
    for router in (health, meta, rankings, teams, games, book, model, matchup):
        app.include_router(router.router)
    # Added innermost first: caching sees the uncompressed JSON (ETag), gzip compresses
    # it, and CORS (outermost) answers preflight requests before anything else runs.
    app.add_middleware(CachingMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["GET"],
        allow_headers=["If-None-Match"],
        expose_headers=["ETag"],
        max_age=86400,
    )
    return app
