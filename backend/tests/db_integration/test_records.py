"""Overall and conference records as the cards show them (#190)."""

from datetime import UTC, datetime

import pytest

from tsi.db.models import Game, Team, TeamSeason
from tsi.db.queries.team_info import Record, records

BEFORE = datetime(2026, 11, 20, tzinfo=UTC)
# id, month/day, home, away, home pts, away pts, conference game, notes
GAMES = [
    (1, (9, 5), 1, 9, 35, 7, False, None),  # non-conference win for team 1
    (2, (10, 3), 1, 2, 28, 21, True, None),  # conference: 1 beats 2
    (3, (10, 17), 3, 1, 24, 17, True, None),  # conference: 3 beats 1
    (4, (11, 7), 2, 3, 20, 20, True, None),  # conference tie (2 and 3)
    (5, (11, 14), 1, 3, 31, 10, True, "Big Conference Championship"),  # title game: not counted
    (6, (11, 28), 1, 2, 40, 0, True, None),  # after `before`: not counted
]


def seed(sessions) -> None:
    with sessions.begin() as s:
        s.add_all([Team(id=t, school=f"T{t}", slug=f"t{t}") for t in (1, 2, 3, 9)])
        s.flush()
        s.add_all(
            TeamSeason(team_id=t, season=2026, division="fbs", conference="Big") for t in (1, 2, 3)
        )
        s.add(TeamSeason(team_id=9, season=2026, division="fcs", conference="Small"))
        s.add_all(
            Game(
                id=g,
                season=2026,
                week=1,
                season_type="regular",
                start_time=datetime(2026, m, d, 18, tzinfo=UTC),
                home_id=h,
                away_id=a,
                home_points=hp,
                away_points=ap,
                completed=True,
                conference_game=conf,
                notes=notes,
            )
            for g, (m, d), h, a, hp, ap, conf, notes in GAMES
        )


@pytest.mark.db
def test_overall_and_conference_records(sessions) -> None:
    seed(sessions)
    with sessions() as s:
        overall = records(s, 2026, BEFORE)
        conf = records(s, 2026, BEFORE, conference_only=True)
        only_one = records(s, 2026, BEFORE, [1], conference_only=True)

    assert overall[1] == Record(3, 1, 0)  # incl. the non-conference and title games
    assert conf[1] == Record(1, 1, 0)  # conference games only, title game excluded
    assert conf[2] == Record(0, 1, 1) and conf[3] == Record(1, 0, 1)
    assert 9 not in conf  # its only game was non-conference
    assert only_one == {1: Record(1, 1, 0)}
