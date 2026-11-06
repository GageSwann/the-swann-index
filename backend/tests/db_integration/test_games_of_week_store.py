"""Games of the week are saved once per poll week and served by the API (decision #141)."""

from datetime import date, timedelta

from tests.db_integration.api_seed import NOW, seed
from tests.db_integration.test_api import make_api

from tsi.services.games_of_week import GameOfWeekPick
from tsi.services.games_of_week_store import needs_picks, save_games_of_week


def pick(game_id: int, kind: str, score: float) -> GameOfWeekPick:
    return GameOfWeekPick("fbs", kind, game_id, score, 0.9, 0.8, 0.3, 4, 2, 0.25, 0.1, None, 0.2)


def test_saved_once_per_poll_week_and_served(sessions) -> None:
    with sessions.begin() as s:
        seed(s)
    with sessions() as s:
        assert needs_picks(s, NOW)

    assert (
        save_games_of_week(sessions, [pick(202, "power", 0.7), pick(202, "resume", 0.6)], 2026, NOW)
        == 2
    )
    # A later run in the same poll week (Wednesday -> Saturday) keeps the first picks.
    assert (
        save_games_of_week(sessions, [pick(201, "power", 0.9)], 2026, NOW + timedelta(days=3)) == 0
    )
    with sessions() as s:
        assert not needs_picks(s, NOW)

    with make_api(sessions) as api:
        body = api.get("/games-of-week").json()
    assert body["poll_date"] == date(2026, 10, 18).isoformat()  # NOW is a Wednesday
    assert [(p["division"], p["ranking_type"]) for p in body["picks"]] == [
        ("fbs", "power"),
        ("fbs", "resume"),
    ]
    first = body["picks"][0]
    assert first["game"]["id"] == 202 and first["game"]["home"]["school"] == "Bravo"
    assert first["game"]["prediction"] is not None  # the board's current snapshot
    assert (first["home_rank"], first["home_playoff_swing"], first["home_title_swing"]) == (
        4,
        0.25,
        None,
    )


def test_empty_before_the_first_pick(sessions) -> None:
    with sessions.begin() as s:
        seed(s)
    with make_api(sessions) as api:
        assert api.get("/games-of-week").json() == {
            "poll_date": None,
            "picked_at": None,
            "picks": [],
        }
