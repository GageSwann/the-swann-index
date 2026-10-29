import pytest

from tsi.config import Settings
from tsi.db.engine import make_engine, sqlalchemy_url

POOLED = "postgresql://u:pooledpw@ep-x-pooler.neon.tech/neondb?sslmode=require"
DIRECT = "postgresql://u:directpw@ep-x.neon.tech/neondb?sslmode=require"


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("postgresql://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("postgres://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("postgresql+psycopg://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
    ],
)
def test_sqlalchemy_url_uses_psycopg_driver(given: str, expected: str) -> None:
    assert sqlalchemy_url(given) == expected


def _settings(**overrides: str) -> Settings:
    values = {"cfbd_api_key": "k", "database_url": POOLED} | overrides
    return Settings(_env_file=None, **values)


def test_engine_picks_pooled_or_direct_url() -> None:
    settings = _settings(database_url_direct=DIRECT)

    assert make_engine(settings).url.host == "ep-x-pooler.neon.tech"
    assert make_engine(settings, direct=True).url.host == "ep-x.neon.tech"


def test_read_only_engine_autocommits_and_recycles() -> None:
    api = make_engine(_settings(), read_only=True)
    jobs = make_engine(_settings())

    assert api.dialect._on_connect_isolation_level == "AUTOCOMMIT"
    assert api.pool._recycle == 240 and not api.pool._pre_ping
    assert jobs.pool._pre_ping  # writers keep transactions and the checkout ping


def test_engine_repr_masks_password() -> None:
    engine = make_engine(_settings())

    assert "pooledpw" not in repr(engine)
    assert "pooledpw" not in str(engine.url)
