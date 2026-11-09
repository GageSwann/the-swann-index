"""usage (from backend/): PYTHONPATH=<this dir> uv run python profile_api.py PATH [PATH ...]

In-process API through the relay: DB bytes per query for each path (warm, second call)."""

import os
import re
import sys
from collections import defaultdict

from meterlib import counters, relay_env

os.environ.update(relay_env())
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import event  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402

import tsi  # noqa: E402,F401
from tsi.config import get_settings  # noqa: E402

get_settings.cache_clear()
from tsi.api.app import create_app  # noqa: E402

stats: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
last = [0]


def key(sql: str) -> str:
    s = re.sub(r"\s+", " ", sql).strip()
    s = re.sub(r"%\(\w+\)s(, %\(\w+\)s)*", "?", s)
    return s[:220]


@event.listens_for(Engine, "before_cursor_execute")
def before(conn, cursor, statement, params, context, executemany):
    last[0] = counters()[0]


@event.listens_for(Engine, "after_cursor_execute")
def after(conn, cursor, statement, params, context, executemany):
    s = stats[key(statement)]
    s[0] += 1
    s[1] += max(cursor.rowcount, 0)
    s[2] += counters()[0] - last[0]


with TestClient(create_app()) as client:
    for path in sys.argv[1:]:
        client.get(path)  # warm any in-process cache
        stats.clear()
        client.get(path)
        total = sum(v[2] for v in stats.values())
        print(f"\n== {path}: {total / 1e3:.1f} KB in {sum(v[0] for v in stats.values())} queries")
        for sql, (calls, rows, down) in sorted(stats.items(), key=lambda kv: -kv[1][2])[:6]:
            print(f"  {down / 1e3:8.1f} KB {calls:3}x {rows:6} rows  {sql[:170]}")
