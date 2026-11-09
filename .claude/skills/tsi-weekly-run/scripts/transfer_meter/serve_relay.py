"""Start `tsi serve` on port 8001 with the database routed through the relay.

usage (from backend/): PYTHONPATH=<this dir> uv run python serve_relay.py
"""

import subprocess
import sys

from meterlib import relay_env

sys.exit(subprocess.call(["uv", "run", "tsi", "serve", "--port", "8001"], env=relay_env()))
