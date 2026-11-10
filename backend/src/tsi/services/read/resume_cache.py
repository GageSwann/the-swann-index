"""The latest run's Résumé context, built once and shared by every team page (#148).

Each team page needs every team's `season` rating in the latest run (for opponents'
ratings and the benchmark): ~40 KB of database reads that are the same for every team.
The nightly site refresh opens ~50 team pages right after a run, so without sharing it
read them ~50 times. A run's ratings never change once saved (rule 2), so the context
for a run is safe to keep until a newer run is shown.

Single-flight (CLAUDE.md, "in-process caches"): one loader builds it while concurrent
requests wait for it, so a burst of team pages after a run reads it once.
"""

import threading

from sqlalchemy.orm import Session

from tsi.db.queries.runs import RunInfo
from tsi.services.read.resume_view import ResumeContext, resume_context


class ResumeCache:
    """One entry: the context of the most recently asked-for run."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._key: tuple[int, object] | None = None
        self._context: ResumeContext | None = None

    def get(self, session: Session, run: RunInfo) -> ResumeContext:
        key = (run.id, run.run_at)
        with self._lock:  # held while loading: concurrent requests wait, then reuse it
            if self._key != key or self._context is None:
                self._context = resume_context(session, run)
                self._key = key
            return self._context
