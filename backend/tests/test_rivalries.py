"""The rivalry list (#211): well formed, and looked up in either order."""

from tsi.rivalries import RIVALRIES, rivalry_name


def test_either_order() -> None:
    assert rivalry_name("alabama", "auburn") == "Iron Bowl"
    assert rivalry_name("auburn", "alabama") == "Iron Bowl"
    assert rivalry_name("alabama", "georgia") is None


def test_pairs_are_unique_and_well_formed() -> None:
    pairs = [frozenset((a, b)) for a, b, _ in RIVALRIES]
    assert len(pairs) == len(set(pairs))  # one name per pair
    for a, b, name in RIVALRIES:
        assert a != b and a == a.lower() and b == b.lower() and " " not in a + b
        assert name.strip() == name and name


def test_game_title_prefers_the_note_then_the_rivalry() -> None:
    from tsi.services.read.game_card import game_title

    assert game_title("Allstate Red River Rivalry", "texas", "oklahoma") == (
        "Allstate Red River Rivalry"  # CFBD's official name wins over our list
    )
    assert game_title(
        "College Football Playoff Quarterfinal at the Allstate Sugar Bowl - Rescheduled from Jan 1",
        "georgia",
        "notre-dame",
    ) == ("College Football Playoff Quarterfinal at the Allstate Sugar Bowl")
    assert game_title(None, "auburn", "alabama") == "Iron Bowl"
    assert game_title("  ", "auburn", "alabama") == "Iron Bowl"
    assert game_title(None, "alabama", "georgia") is None
