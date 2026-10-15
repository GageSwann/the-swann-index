"""`tsi ingest ...`: pull CFBD data into the database (cache-first, idempotent).

Commands register themselves on `app` when their modules are imported.
"""

from tsi.cli.ingest import jobs, loaders  # noqa: F401  (registers commands)
from tsi.cli.ingest.app import app

__all__ = ["app"]
