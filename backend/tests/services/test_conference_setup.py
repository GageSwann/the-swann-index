from datetime import UTC, datetime, timedelta

from tsi.db.queries.conference import ConferenceGameRow, Member
from tsi.services.conference_setup import build_conferences
from tsi.sim.standings import ConferenceGame

NOW = datetime(2026, 11, 1, tzinfo=UTC)


def row(gid, home, away, hp=None, ap=None, days=-7, conf=True, notes=None) -> ConferenceGameRow:
    done = hp is not None
    return ConferenceGameRow(gid, NOW + timedelta(days=days), home, away, hp, ap, done, conf, notes)


MEMBERS = [
    Member(10, "Sun Belt", "East"),
    Member(11, "Sun Belt", "East"),
    Member(12, "Sun Belt", "West"),
    Member(13, "Sun Belt", "West"),
    Member(20, "Big Ten", None),
    Member(21, "Big Ten", None),
    Member(30, "FBS Independents", None),
]
INDEX = {t: i for i, t in enumerate([10, 11, 12, 13, 20, 21, 30, 99])}


def build(games):
    return {
        c.name: c
        for c in build_conferences(MEMBERS, games, INDEX, {2: 0, 5: 1}, lambda a, b: a - b, NOW)
    }


def test_standings_title_game_and_divisions() -> None:
    confs = build(
        [
            row(1, 10, 11, 21, 14),  # finished: home won
            row(2, 12, 13, days=3),  # remaining: simulated column 0
            row(3, 10, 99, 35, 0, conf=False),  # non-member opponent: ignored
            row(4, 20, 21, 7, 7),  # tie: doesn't count
            row(5, 11, 13, days=30, conf=False, notes="Sun Belt Championship"),  # column 1
        ]
    )

    assert set(confs) == {"Big Ten", "Sun Belt"}  # independents have no title game
    sb = confs["Sun Belt"]
    assert sb.teams == (0, 1, 2, 3)
    assert sb.games == (ConferenceGame(0, 1, home_won=True), ConferenceGame(2, 3, column=0))
    assert sb.title_game == ConferenceGame(1, 3, column=1)
    assert sb.divisions == ((0, 1), (2, 3))  # East, West
    assert sb.neutral_margin[0, 2] == -2 and sb.neutral_margin[2, 0] == 2
    assert confs["Big Ten"].games == () and confs["Big Ten"].divisions is None


def test_unplayed_past_games_dont_count() -> None:
    confs = build([row(1, 10, 11, days=-3)])  # kicked off, never completed (postponed)

    assert confs["Sun Belt"].games == ()
