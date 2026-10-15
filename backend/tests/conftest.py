import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def cfbd_fixture() -> Callable[[str], Any]:
    """Load a saved CFBD response from tests/fixtures/cfbd/<name>.json."""

    def load(name: str) -> Any:
        return json.loads((FIXTURES / "cfbd" / f"{name}.json").read_text(encoding="utf-8"))

    return load
