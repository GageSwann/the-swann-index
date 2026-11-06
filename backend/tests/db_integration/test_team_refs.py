"""Team display info carries corrected colors (Phase 13.2, decision #138)."""

from tsi.db.models import Team
from tsi.db.queries.team_info import team_refs


def test_team_refs_apply_color_corrections(sessions) -> None:
    with sessions.begin() as s:
        s.add_all(
            [
                Team(id=12, school="Arizona", slug="arizona", color="#cc0033", alt_color="#003366"),
                Team(
                    id=333, school="Alabama", slug="alabama", color="#9e1b32", alt_color="#ffffff"
                ),
            ]
        )
    with sessions() as s:
        refs = team_refs(s, 2026)
    assert (refs[12].color, refs[12].alt_color) == ("#AB0520", "#0C234B")
    assert (refs[333].color, refs[333].alt_color) == ("#9e1b32", "#ffffff")
