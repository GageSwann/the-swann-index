import threading
import time
from datetime import UTC, datetime

import pytest

from tsi.services.read import matchup


def test_live_inputs_load_once_under_concurrent_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def slow_load(session, season, now, artifact):
        calls.append(season)
        time.sleep(0.2)  # long enough for every thread to arrive while loading
        return f"inputs-{season}"

    monkeypatch.setattr(matchup, "load_live_inputs", slow_load)
    monkeypatch.setattr(matchup, "_cache", {})
    now = datetime(2026, 10, 21, 12, tzinfo=UTC)
    results = []
    threads = [
        threading.Thread(
            target=lambda: results.append(matchup._live_inputs(None, 2026, now, None))  # type: ignore[arg-type]
        )
        for _ in range(8)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert calls == [2026]
    assert results == ["inputs-2026"] * 8
