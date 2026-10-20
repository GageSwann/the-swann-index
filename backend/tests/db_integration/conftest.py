"""Database-backed tests: each session gets a throwaway schema in the configured database.

Tables are created fresh in `test_<random>` (via search_path) and the schema is
dropped afterwards, so real tables are never touched. Skipped when no database
is configured (e.g. CI without secrets). CFBD is faked; no API calls are made.
"""

import importlib.util
import uuid
from collections.abc import Callable, Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import Engine, event, text
from sqlalchemy.orm import Session, sessionmaker

import tsi.db.models  # noqa: F401  (registers tables)
from tsi.config import ConfigError, load_settings
from tsi.db.base import Base
from tsi.db.engine import make_engine, make_session_factory
from tsi.ingest.cache import CachedResponse

MIGRATIONS = Path(__file__).parents[2] / "alembic" / "versions"


@pytest.fixture(scope="session")
def db_engine() -> Iterator[Engine]:
    try:
        settings = load_settings()
    except ConfigError:
        pytest.skip("no database configured")
    schema = f"test_{uuid.uuid4().hex[:10]}"
    engine = make_engine(settings, direct=True)

    @event.listens_for(engine, "connect")
    def _use_test_schema(dbapi_conn: Any, _record: Any) -> None:
        with dbapi_conn.cursor() as cursor:
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
            cursor.execute(f'SET search_path TO "{schema}"')
        dbapi_conn.commit()

    try:
        Base.metadata.create_all(engine)
        _install_immutability_trigger(engine)
        yield engine
    finally:
        engine.dispose()
        cleanup = make_engine(settings, direct=True)
        with cleanup.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        cleanup.dispose()


def _install_immutability_trigger(engine: Engine) -> None:
    """Rule 2's trigger lives in the initial migration, not the ORM models; load that SQL."""
    path = next(MIGRATIONS.glob("*_initial_schema.py"))
    spec = importlib.util.spec_from_file_location("initial_schema", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with engine.begin() as conn:
        conn.execute(text(migration.PREDICTIONS_IMMUTABLE_FN))
        conn.execute(
            text(
                "CREATE TRIGGER predictions_immutable BEFORE UPDATE OR DELETE ON predictions "
                "FOR EACH ROW EXECUTE FUNCTION tsi_predictions_immutable()"
            )
        )


@pytest.fixture
def sessions(db_engine: Engine) -> Iterator[sessionmaker[Session]]:
    """Fresh, empty tables for each test."""
    with db_engine.begin() as conn:
        names = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
        conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))
    yield make_session_factory(db_engine)


class FakeCfbd:
    """Stands in for CfbdClient: serves saved fixtures keyed by (endpoint, params)."""

    def __init__(self, responses: Mapping[tuple[str, frozenset], Any], fetched_at: datetime):
        self.responses = dict(responses)
        self.fetched_at = fetched_at
        self.calls: list[tuple[str, dict]] = []

    def get_response(
        self, endpoint: str, params: Mapping[str, Any] | None = None, *, refresh: bool = False
    ) -> CachedResponse:
        clean = {k: v for k, v in (params or {}).items() if v is not None}
        self.calls.append((endpoint, clean))
        return CachedResponse(self.responses[(endpoint, frozenset(clean.items()))], self.fetched_at)

    def get(self, endpoint: str, params: Mapping[str, Any] | None = None, **kw: Any) -> Any:
        return self.get_response(endpoint, params, **kw).data


@pytest.fixture
def fake_cfbd(cfbd_fixture: Callable[[str], Any]) -> FakeCfbd:
    """All 2024 sample fixtures, as if fetched long after the season (closing lines)."""
    year = frozenset({("year", 2024)})
    return FakeCfbd(
        {
            ("/venues", frozenset()): cfbd_fixture("venues_sample"),
            ("/teams", year): cfbd_fixture("teams_2024_sample"),
            ("/calendar", year): cfbd_fixture("calendar_2024_sample"),
            ("/games", year | {("seasonType", "both")}): cfbd_fixture("games_2024_sample"),
            ("/stats/game/advanced", year | {("excludeGarbageTime", "true")}): cfbd_fixture(
                "advanced_2024_filtered_sample"
            ),
            ("/stats/game/advanced", year): cfbd_fixture("advanced_2024_full_sample"),
            ("/lines", year): cfbd_fixture("lines_2024_sample"),
            ("/talent", year): cfbd_fixture("talent_2024_sample"),
            ("/player/returning", year): cfbd_fixture("returning_2024_sample"),
            # Roster inputs: classes 2021-24, portal 2024, coaches 2024 and 2023.
            **{("/recruiting/teams", frozenset({("year", y)})): [] for y in range(2021, 2025)},
            ("/recruiting/teams", year): [{"year": 2024, "team": "Colorado", "points": 249.0}],
            ("/player/portal", year): [],
            ("/coaches", year): [],
            ("/coaches", frozenset({("year", 2023)})): [],
        },
        fetched_at=datetime(2026, 10, 14, tzinfo=UTC),
    )
