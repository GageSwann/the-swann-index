"""Run a command with the DB routed through the relay; print bytes the DB sent.

usage: python run_cmd.py LABEL -- cmd args...   (run from backend/ with `uv run`)
"""

import subprocess
import sys
import time

from meterlib import counters, mb, relay_env

label = sys.argv[1]
cmd = sys.argv[sys.argv.index("--") + 1 :]
env = relay_env()
d0, u0, c0 = counters()
t0 = time.time()
proc = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
d1, u1, c1 = counters()
print(
    f"{label}: down {mb(d1 - d0)}, up {mb(u1 - u0)}, connections {c1 - c0}, "
    f"{time.time() - t0:.0f}s, exit {proc.returncode}"
)
with open(f"{label}.log", "w", encoding="utf-8") as f:
    f.write(proc.stdout + proc.stderr)
