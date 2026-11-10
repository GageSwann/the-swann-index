"""The saved Elo state round-trips exactly and is used only where it applies (#146)."""

from dataclasses import replace

from tsi.model.elo import EloParams, EloRun
from tsi.model.elo_carry import EloCarry, load_carry, rating_params, save_carry


def carry(params: EloParams | None = None) -> EloCarry:
    run = EloRun([], {1: 1612.3456789012345, 7: 1000.1 / 3}, {1: "fbs", 7: "ii"}, 2025)
    return EloCarry(2025, "abc", rating_params(params or EloParams()), run)


def test_round_trip_is_exact(tmp_path) -> None:
    path = tmp_path / "elo_carry.json"
    save_carry(carry(), path)
    loaded = load_carry(path)
    assert loaded == carry()
    assert path.read_bytes().count(b"\r") == 0  # LF on every OS


def test_missing_file_is_none(tmp_path) -> None:
    assert load_carry(tmp_path / "none.json") is None


def test_usable_only_for_the_next_season_with_the_same_params() -> None:
    params = EloParams()
    assert carry().usable(2026, params)
    assert not carry().usable(2025, params)
    assert not carry().usable(2027, params)
    assert not carry().usable(2026, replace(params, k=40.0))
    assert carry().usable(2026, replace(params, elo_per_point=25.0))  # scale only
