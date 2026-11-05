"""FCS playoff inputs: who can't be picked (moving up), and when the real field is set."""

from datetime import UTC, datetime

import pytest

from tsi.db.models import Game, Team, TeamSeason
from tsi.db.queries.conference import conference_members, fcs_playoff_games, moved_up_teams

# team -> division by season
HISTORY = {
    1: {2022: "ii", 2023: "ii", 2024: "fcs", 2025: "fcs", 2026: "fcs"},  # moved up in 2024
    2: {2020: "ii", 2021: "fcs", 2022: "fcs", 2026: "fcs"},  # moved up in 2021: eligible now
    3: {2022: "fbs", 2023: "fcs", 2026: "fcs"},  # came down from FBS: eligible
    4: {2025: "fcs", 2026: "fcs"},  # new program, no lower-division seasons: eligible
    5: {2026: "fbs"},
}


@pytest.mark.db
def test_moved_up_teams_and_the_playoff_field(sessions) -> None:
    with sessions.begin() as s:
        s.add_all([Team(id=t, school=f"T{t}", slug=f"t{t}") for t in HISTORY])
        s.flush()
        s.add_all(
            TeamSeason(team_id=t, season=y, division=d, conference="C")
            for t, seasons in HISTORY.items()
            for y, d in seasons.items()
        )
        s.add(
            Game(
                id=10,
                season=2026,
                week=14,
                season_type="regular",
                start_time=datetime(2026, 11, 28, 18, tzinfo=UTC),
                home_id=2,
                away_id=3,
                completed=False,
                notes="FCS Championship - First Round",
            )
        )

    with sessions() as s:
        assert moved_up_teams(s, 2026, 4) == {1}
        assert moved_up_teams(s, 2024, 4) == {1, 2}
        assert fcs_playoff_games(s, 2026) == {10}
        assert fcs_playoff_games(s, 2025) == set()
        members = conference_members(s, 2026, ("fbs", "fcs"))
        assert {(m.team_id, m.division) for m in members} == {
            (1, "fcs"),
            (2, "fcs"),
            (3, "fcs"),
            (4, "fcs"),
            (5, "fbs"),
        }
        assert [m.team_id for m in conference_members(s, 2026)] == [5]  # FBS by default
