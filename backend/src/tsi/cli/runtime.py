"""Shared CLI wiring: settings -> engine -> sessions -> CFBD client, with friendly errors."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager

import typer
from sqlalchemy.orm import Session, sessionmaker

from tsi.config import ConfigError, get_settings
from tsi.db.engine import make_engine, make_session_factory
from tsi.ingest.client import CfbdClient, CfbdError
from tsi.ingest.factory import make_cfbd_client


def configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


@contextmanager
def ingest_runtime() -> Iterator[tuple[CfbdClient, sessionmaker[Session]]]:
    """Yield a CFBD client and session factory; turn known failures into clean exits."""
    try:
        settings = get_settings()
    except ConfigError as exc:
        typer.secho(str(exc), fg="red", err=True)
        raise typer.Exit(1) from None

    engine = make_engine(settings)
    try:
        sessions = make_session_factory(engine)
        with make_cfbd_client(settings, sessions) as client:
            yield client, sessions
    except CfbdError as exc:
        typer.secho(f"CFBD error: {exc}", fg="red", err=True)
        raise typer.Exit(1) from None
    finally:
        engine.dispose()
