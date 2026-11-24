"""Which game a team page's Next Game card shows (#199)."""

from datetime import UTC, datetime

from tsi.db.queries.games import GameRow
from tsi.services.read.teams import _next_game


def _game(gid: int, day: int | None, hp: int | None = None, ap: int | None = None, done=False):
    return GameRow(
        id=gid,
        season=2026,
        week=day or 0,
        season_type="regular",
        start_time=datetime(2026, 9, day, 19, tzinfo=UTC) if day else None,
        start_time_tbd=False,
        home_id=1,
        away_id=2,
        neutral=False,
        conference_game=False,
        completed=done,
        home_points=hp,
        away_points=ap,
        notes=None,
    )


def test_first_game_not_final_by_kickoff() -> None:
    games = [_game(3, 20), _game(1, 6, 30, 20, done=True), _game(2, 13)]
    assert _next_game(games).id == 2  # input order doesn't matter


def test_a_game_in_progress_is_still_next() -> None:
    games = [_game(1, 6, 30, 20, done=True), _game(2, 13, 7, 3), _game(3, 20)]
    assert _next_game(games).id == 2  # scored but not completed


def test_all_final_shows_the_last_game_played() -> None:
    games = [_game(2, 13, 14, 10, done=True), _game(1, 6, 30, 20, done=True)]
    assert _next_game(games).id == 2


def test_a_game_without_a_kickoff_comes_last() -> None:
    games = [_game(9, None), _game(1, 6, 30, 20, done=True)]
    assert _next_game(games).id == 9  # the only unfinished game
    assert _next_game([_game(9, None), _game(2, 13)]).id == 2


def test_no_games() -> None:
    assert _next_game([]) is None
