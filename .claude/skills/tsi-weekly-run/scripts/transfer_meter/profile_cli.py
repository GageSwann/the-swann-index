"""Run a `tsi` CLI command in-process through the relay and attribute DB bytes per query.

usage (from backend/): uv run python profile_cli.py OUT.csv run [--no-ingest ...]
Writes one row per distinct SQL text: calls, rows, bytes down.
"""

import csv
import os
import re
import sys
from collections import defaultdict

from meterlib import counters, mb, relay_env

os.environ.update(relay_env())
from sqlalchemy import event  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402

import tsi  # noqa: E402,F401
from tsi.config import get_settings  # noqa: E402

get_settings.cache_clear()

stats: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])  # calls, rows, bytes
last = [counters()[0]]


def key(sql: str) -> str:
    s = re.sub(r"\s+", " ", sql).strip()
    s = re.sub(r"%\(\w+\)s(, %\(\w+\)s)*", "?", s)
    s = re.sub(r"\$\d+(, \$\d+)*", "?", s)
    return s[:400]


@event.listens_for(Engine, "before_cursor_execute")
def before(conn, cursor, statement, params, context, executemany):
    last[0] = counters()[0]


@event.listens_for(Engine, "after_cursor_execute")
def after(conn, cursor, statement, params, context, executemany):
    down = counters()[0] - last[0]
    s = stats[key(statement)]
    s[0] += 1
    s[1] += max(cursor.rowcount, 0)
    s[2] += down


out = sys.argv[1]
from tsi.cli.main import app  # noqa: E402

start = counters()[0]
try:
    app(sys.argv[2:], standalone_mode=False)
finally:
    total = counters()[0] - start
    rows = sorted(stats.items(), key=lambda kv: -kv[1][2])
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bytes", "calls", "rows", "sql"])
        for sql, (calls, nrows, down) in rows:
            w.writerow([down, calls, nrows, sql])
    attributed = sum(v[2] for v in stats.values())
    print(f"total down {mb(total)}, attributed to queries {mb(attributed)}", file=sys.stderr)
    for sql, (calls, nrows, down) in rows[:25]:
        print(f"{mb(down):>10} {calls:>5}x {nrows:>7} rows  {sql[:150]}", file=sys.stderr)
