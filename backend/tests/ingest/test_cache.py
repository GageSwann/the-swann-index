from datetime import UTC, datetime
from pathlib import Path

from tsi.ingest.cache import DiskCache, cache_key


def test_round_trip_keeps_data_and_fetch_time(tmp_path: Path) -> None:
    cache = DiskCache(tmp_path)
    fetched = datetime(2026, 10, 14, 20, 0, tzinfo=UTC)
    cache.put("/games", {"year": 2024}, [{"id": 1}], fetched_at=fetched)

    entry = cache.get("/games", {"year": 2024})

    assert entry is not None
    assert entry.data == [{"id": 1}]
    assert entry.fetched_at == fetched


def test_missing_entry_returns_none(tmp_path: Path) -> None:
    assert DiskCache(tmp_path).get("/games", {"year": 2024}) is None


def test_key_ignores_param_order_but_not_values() -> None:
    a = cache_key("/games", {"year": 2024, "week": 1})
    b = cache_key("/games", {"week": 1, "year": 2024})
    c = cache_key("/games", {"year": 2024, "week": 2})

    assert a == b
    assert a != c


def test_files_grouped_by_endpoint(tmp_path: Path) -> None:
    path = DiskCache(tmp_path).path_for("/stats/game/advanced", {"year": 2024})

    assert path.parent == tmp_path / "cfbd" / "stats_game_advanced"
