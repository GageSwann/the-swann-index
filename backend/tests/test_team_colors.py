"""The team color corrections table (Phase 13.2, decision #138)."""

import re

from tsi.team_colors import FIXES, corrected_colors

HEX = re.compile(r"^#[0-9A-F]{6}$")


def test_every_fix_is_a_hex_color_with_a_source() -> None:
    for fix in FIXES:
        assert HEX.match(fix.color), fix
        assert fix.alt_color is None or HEX.match(fix.alt_color), fix
        assert fix.source.startswith("https://"), fix


def test_one_fix_per_team() -> None:
    ids = [fix.team_id for fix in FIXES]
    assert len(ids) == len(set(ids))


def test_corrected_colors_replace_cfbd_only_for_listed_teams() -> None:
    assert corrected_colors(12, "#cc0033", "#003366") == ("#AB0520", "#0C234B")  # Arizona
    assert corrected_colors(333, "#9e1b32", "#ffffff") == ("#9e1b32", "#ffffff")  # Alabama
