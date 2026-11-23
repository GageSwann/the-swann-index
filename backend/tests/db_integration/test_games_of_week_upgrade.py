"""A game added after the week's picks can replace one (#157): the FCS playoff's next
round is announced on Sunday afternoon, after the morning's picks."""

from datetime import timedelta

from sqlalchemy import update
from tests.db_integration.api_seed import NOW, UPCOMING_KICKOFF, seed

from tsi.db.models import Game, GameOfWeek
from tsi.db.queries.games_of_week import games_added_since, picks_for
from tsi.services.games_of_week import GameOfWeekPick, poll_sunday
from tsi.services.games_of_week_store import save_games_of_week, upgrade_games_of_week


def pick(game_id: int, home_rank: int, away_rank: int) -> GameOfWeekPick:
    return GameOfWeekPick("fbs", "power", game_id, 0.5, 0.5, 0.9, 0.0, home_rank, away_rank,
                          None, None, None, None)  # fmt: skip


def setup(sessions) -> None:
    with sessions.begin() as s:
        seed(s)
        kickoff = UPCOMING_KICKOFF + timedelta(hours=2)
        s.add(Game(id=204, season=2026, week=8, season_type="regular", start_time=kickoff,
                   home_id=1, away_id=3))  # fmt: skip
        s.flush()
        s.execute(update(Game).values(created_at=NOW - timedelta(days=20)))
        s.execute(update(Game).where(Game.id == 204).values(created_at=NOW + timedelta(hours=6)))
    save_games_of_week(sessions, [pick(202, 10, 20)], 2026, NOW)


def stored_game(sessions) -> int:
    with sessions() as s:
        return picks_for(s, poll_sunday(NOW))[0].game_id


def test_only_games_added_after_the_pick_count(sessions) -> None:
    setup(sessions)
    with sessions() as s:
        assert games_added_since(s, [201, 202, 204], NOW) == {204}


def test_a_better_added_game_replaces_the_pick(sessions) -> None:
    setup(sessions)
    later = NOW + timedelta(days=1)

    assert upgrade_games_of_week(sessions, [pick(204, 30, 40)], later) == []  # worse: kept
    assert stored_game(sessions) == 202

    assert [p.game_id for p in upgrade_games_of_week(sessions, [pick(204, 3, 5)], later)] == [204]
    with sessions() as s:
        row = s.query(GameOfWeek).one()
    assert (row.game_id, row.home_rank, row.away_rank, row.picked_at) == (204, 3, 5, later)


def test_a_pick_that_kicked_off_stays(sessions) -> None:
    setup(sessions)
    after_kickoff = UPCOMING_KICKOFF + timedelta(minutes=5)

    assert upgrade_games_of_week(sessions, [pick(204, 1, 2)], after_kickoff) == []
    assert stored_game(sessions) == 202
