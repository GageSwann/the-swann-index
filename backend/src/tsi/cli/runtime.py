"""Shared CLI wiring: settings -> engine -> sessions (-> CFBD client), with clean exits.

Known failures (bad config, CFBD errors) print a short red message and exit 1
instead of a traceback. Messages never include secret values.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager

import typer
from sqlalchemy.orm import Session, sessionmaker

from tsi.config import ConfigError, Settings, get_settings
from tsi.db.engine import make_engine, make_session_factory
from tsi.ingest.client import CfbdClient
from tsi.ingest.errors import CfbdError
from tsi.ingest.factory import make_cfbd_client


def configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def fail(message: str) -> typer.Exit:
    typer.secho(message, fg="red", err=True)
    return typer.Exit(1)


def load_settings_or_exit() -> Settings:
    try:
        return get_settings()
    except ConfigError as exc:
        raise fail(str(exc)) from None


@contextmanager
def db_runtime() -> Iterator[sessionmaker[Session]]:
    """Yield a session factory; the engine is disposed afterwards."""
    engine = make_engine(load_settings_or_exit())
    try:
        yield make_session_factory(engine)
    finally:
        engine.dispose()


@contextmanager
def ingest_runtime() -> Iterator[tuple[CfbdClient, sessionmaker[Session]]]:
    """Yield a CFBD client and session factory; CFBD failures become clean exits."""
    settings = load_settings_or_exit()
    with db_runtime() as sessions:
        try:
            with make_cfbd_client(settings, sessions) as client:
                yield client, sessions
        except CfbdError as exc:
            raise fail(f"CFBD error: {exc}") from None
