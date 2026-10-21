"""The OpenAPI document, committed at docs/api/openapi.json (source for the web's TS types).

Built without settings or a database. `tests/api/test_openapi.py` fails if the
committed file and the code ever disagree; regenerate with `tsi openapi`.
"""

import json
from pathlib import Path
from typing import Any

from tsi.api.app import build_app

REPO_ROOT = Path(__file__).resolve().parents[4]
SPEC_PATH = REPO_ROOT / "docs" / "api" / "openapi.json"


def openapi_document() -> dict[str, Any]:
    return build_app(cors_origins=[]).openapi()


def render(document: dict[str, Any]) -> str:
    """Stable text: sorted keys, 2-space indent, trailing newline (clean diffs)."""
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_openapi(path: Path = SPEC_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(openapi_document()), encoding="utf-8", newline="\n")
    return path
