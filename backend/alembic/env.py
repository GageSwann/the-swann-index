"""Alembic environment. The database URL comes from tsi.config, never alembic.ini."""

from logging.config import fileConfig

from alembic import context

import tsi.db.models  # noqa: F401  (registers every table on Base.metadata)
from tsi.config import get_settings
from tsi.db.base import Base
from tsi.db.engine import make_engine, sqlalchemy_url

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout (`alembic upgrade head --sql`) without connecting."""
    url = sqlalchemy_url(get_settings().migration_database_url.get_secret_value())
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = make_engine(get_settings(), direct=True)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
