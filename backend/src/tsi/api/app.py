"""FastAPI application factory. Run locally with `tsi serve`; export the spec with `tsi openapi`."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from anyio import to_thread
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from tsi import __version__
from tsi.api.caching import CachingMiddleware
from tsi.api.routers import (
    book,
    games,
    games_of_week,
    health,
    meta,
    model,
    playoff,
    rankings,
    teams,
)
from tsi.config import Settings, get_settings
from tsi.db.engine import make_engine, make_session_factory
from tsi.services.read.resume_cache import ResumeCache

TITLE = "The Swann Index API"
# Requests handled at once (sync endpoints run in a thread each). Kept below the engine's
# connection pool (SQLAlchemy's default 5 + 10 overflow) so a request never waits for a
# connection: under a burst (a site build) extra requests queue for a thread, which has no
# timeout, instead of failing after the pool's 30 s wait (decision #102).
CONCURRENT_REQUESTS = 10
DESCRIPTION = "Read-only college football ratings, rankings and predictions."


def create_app(settings: Settings | None = None) -> FastAPI:
    """The served app: settings (database, CORS origins) are resolved now."""
    settings = settings or get_settings()
    app = build_app(settings.tsi_cors_origins, settings)
    app.state.owner_key = settings.owner_api_key  # unset: private endpoints always 404
    return app


def build_app(cors_origins: list[str], settings: Settings | None = None) -> FastAPI:
    """App without reading settings until it starts (so the spec can be built anywhere)."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = make_engine(settings or get_settings(), read_only=True)
        app.state.sessions = make_session_factory(engine)
        to_thread.current_default_thread_limiter().total_tokens = CONCURRENT_REQUESTS
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
    app.state.resume_cache = ResumeCache()  # per app: the latest run's Résumé context (#148)
    for router in (
        health,
        meta,
        rankings,
        teams,
        games,
        games_of_week,
        book,
        model,
        playoff,
    ):
        app.include_router(router.router)
    # Added innermost first: caching sees the uncompressed JSON (ETag), gzip compresses
    # it, and CORS (outermost) answers preflight requests before anything else runs.
    app.add_middleware(CachingMiddleware)
    # Level 1, not Starlette's 9: about a quarter of the CPU (Render has 0.1 CPU) for
    # responses ~25% larger, e.g. all-division rankings 45 KB instead of 35 KB.
    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=1)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["GET"],
        allow_headers=[
            "If-None-Match"
        ],  # no Authorization: the owner's key never comes from a browser
        expose_headers=["ETag"],
        max_age=86400,
    )
    return app
