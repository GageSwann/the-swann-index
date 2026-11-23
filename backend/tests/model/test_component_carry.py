"""Last season's saved component fit round-trips exactly and is used only where it applies."""

from tsi.model.component_carry import ComponentCarry, load_carry, save_carry
from tsi.model.ratings.components import Components, MetricRatings
from tsi.model.ratings.types import TeamRating


def metric(x: float) -> MetricRatings:
    # Keys out of order and a pooled team: the loaded dict keeps the fit's order.
    teams = {
        7: TeamRating(x / 3, -x / 7),
        1: TeamRating(0.1 + x, 2 / 3),
        -2: TeamRating(-9.0, 1e-17),
    }
    return MetricRatings(teams, hfa=x / 11, level=25.123456789012345 + x)


def carry() -> ComponentCarry:
    components = Components(
        ppd=metric(1.0),
        success=metric(2.0),
        pace=metric(3.0),
        tempo=None,
        games={7: 12, 1: 13},
        second=metric(4.0),
        power=None,
    )
    return ComponentCarry(2025, "abc", 2.0, "tsi-v1.7", components)


def test_round_trip_is_exact(tmp_path) -> None:
    path = tmp_path / "component_carry.json"
    save_carry(carry(), path)
    loaded = load_carry(path)
    assert loaded == carry()
    assert repr(loaded) == repr(carry())  # same values, same key order
    assert path.read_bytes().count(b"\r") == 0  # LF on every OS


def test_missing_file_is_none(tmp_path) -> None:
    assert load_carry(tmp_path / "none.json") is None


def test_usable_only_for_the_next_season_with_the_same_fit() -> None:
    assert carry().usable(2026, 2.0, "tsi-v1.7")
    assert not carry().usable(2025, 2.0, "tsi-v1.7")
    assert not carry().usable(2027, 2.0, "tsi-v1.7")
    assert not carry().usable(2026, 3.0, "tsi-v1.7")
    assert not carry().usable(2026, 2.0, "tsi-v1.8")
