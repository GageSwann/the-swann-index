"""The latest run's Résumé context is built once per run and shared (#148)."""

from datetime import UTC, datetime
from threading import Thread

from tsi.db.queries.runs import RunInfo
from tsi.services.read import resume_cache
from tsi.services.read.resume_cache import ResumeCache


def run(run_id: int, hour: int = 11) -> RunInfo:
    return RunInfo(run_id, 2026, "regular", 11, datetime(2026, 11, 9, hour, tzinfo=UTC), "v")


def test_built_once_per_run_and_rebuilt_for_a_newer_one(monkeypatch) -> None:
    built: list[int] = []

    def fake(session, r):
        built.append(r.id)
        return f"context {r.id}"

    monkeypatch.setattr(resume_cache, "resume_context", fake)
    cache = ResumeCache()
    threads = [Thread(target=lambda: cache.get(None, run(7))) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert cache.get(None, run(7)) == "context 7"
    assert built == [7]  # eight concurrent requests, one build

    assert cache.get(None, run(8)) == "context 8"
    assert cache.get(None, run(8, hour=12)) == "context 8"  # same id, another time: rebuilt
    assert built == [7, 8, 8]
