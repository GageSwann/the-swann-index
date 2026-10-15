import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
DB_TESTS = Path(__file__).parent / "db_integration"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Everything under tests/db_integration/ gets the `db` marker (skip with -m "not db")."""
    for item in items:
        if DB_TESTS in Path(item.path).parents:
            item.add_marker(pytest.mark.db)


@pytest.fixture
def cfbd_fixture() -> Callable[[str], Any]:
    """Load a saved CFBD response from tests/fixtures/cfbd/<name>.json."""

    def load(name: str) -> Any:
        return json.loads((FIXTURES / "cfbd" / f"{name}.json").read_text(encoding="utf-8"))

    return load
