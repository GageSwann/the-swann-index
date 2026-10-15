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


def make_engine(settings: Settings, *, direct: bool = False) -> Engine:
    """Pooled URL by default; `direct=True` for migrations and bulk loads."""
    secret = settings.migration_database_url if direct else settings.database_url
    return create_engine(
        sqlalchemy_url(secret.get_secret_value()),
        pool_pre_ping=True,  # Neon suspends idle computes; reconnect transparently
        hide_parameters=True,  # keep bound values out of error messages and logs
    )


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
