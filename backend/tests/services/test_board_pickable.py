from datetime import UTC, datetime

from tsi.db.queries.schedule import UpcomingGame
from tsi.services.board import pickable

KICKOFF = datetime(2026, 11, 7, 17, tzinfo=UTC)


def game(home_div: str, away_div: str) -> UpcomingGame:
    return UpcomingGame(1, 2026, 11, "regular", KICKOFF, 10, 20, home_div, away_div, False)


def test_only_fbs_vs_fbs_games_can_be_picks() -> None:
    assert pickable(game("fbs", "fbs"))
    assert not pickable(game("fbs", "fcs"))  # e.g. Wake Forest vs. Merrimack
    assert not pickable(game("fcs", "fbs"))
    assert not pickable(game("fbs", "ii"))
