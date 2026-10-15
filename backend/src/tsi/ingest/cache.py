"""On-disk cache of raw CFBD JSON responses (default `backend/.cache/`, gitignored).

One file per (endpoint, params) pair. Only response bodies are stored; never
request headers, so the API key cannot end up in the cache. Whether an entry is
still usable is decided by `tsi.ingest.freshness`, not here.
"""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CachedResponse:
    data: Any
    fetched_at: datetime


def cache_key(endpoint: str, params: Mapping[str, Any]) -> str:
    """Stable key: parameter order doesn't matter."""
    canonical = json.dumps(
        {"endpoint": endpoint, "params": dict(params)}, sort_keys=True, default=str
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


class DiskCache:
    def __init__(self, root: Path) -> None:
        self.root = root

    def path_for(self, endpoint: str, params: Mapping[str, Any]) -> Path:
        folder = endpoint.strip("/").replace("/", "_") or "root"
        return self.root / "cfbd" / folder / f"{cache_key(endpoint, params)}.json"

    def get(self, endpoint: str, params: Mapping[str, Any]) -> CachedResponse | None:
        path = self.path_for(endpoint, params)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return CachedResponse(payload["data"], datetime.fromisoformat(payload["fetched_at"]))

    def put(
        self,
        endpoint: str,
        params: Mapping[str, Any],
        data: Any,
        *,
        fetched_at: datetime | None = None,
    ) -> None:
        path = self.path_for(endpoint, params)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "endpoint": endpoint,
            "params": dict(params),
            "fetched_at": (fetched_at or datetime.now(UTC)).isoformat(),
            "data": data,
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        tmp.replace(path)  # atomic: a crash never leaves a half-written cache file
