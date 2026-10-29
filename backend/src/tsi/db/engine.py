"""Engine and session factories. Connection strings come only from `Settings`."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from tsi.config import Settings

_DRIVER_PREFIXES = ("postgresql://", "postgres://")


def sqlalchemy_url(url: str) -> str:
    """Neon hands out `postgresql://...`; SQLAlchemy needs the psycopg (v3) driver name."""
    for prefix in _DRIVER_PREFIXES:
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url.removeprefix(prefix)
    return url


def make_engine(settings: Settings, *, direct: bool = False, read_only: bool = False) -> Engine:
    """Pooled URL by default; `direct=True` for migrations and bulk loads.

    `read_only=True` is the API's engine. It autocommits: no BEGIN before a request's first
    query and no ROLLBACK when its session closes (each statement already reads its own
    snapshot under Postgres's default READ COMMITTED). Every engine pings a connection
    before handing it out: Neon can drop idle connections (computes suspend), and the ping
    costs one few-millisecond round trip in production (decision #99).
    """
    secret = settings.migration_database_url if direct else settings.database_url
    return create_engine(
        sqlalchemy_url(secret.get_secret_value()),
        pool_pre_ping=True,  # reconnect transparently when Neon has closed a connection
        hide_parameters=True,  # keep bound values out of error messages and logs
        **({"isolation_level": "AUTOCOMMIT"} if read_only else {}),
    )


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
