"""Games of the week: the poll week, the window and the pick (decision #141)."""

from datetime import UTC, date, datetime

import pytest

from tsi.db.queries.schedule import UpcomingGame
from tsi.model.distribution import ScoreDistribution
from tsi.services.compute_rankings import Rankings, TeamRanking
from tsi.services.games_of_week import pick_games_of_week, poll_sunday, window_end
from tsi.services.predict import GameForecast
from tsi.sim.stakes import GameStakes, TeamStakes

NOW = datetime(2026, 11, 8, 11, 0, tzinfo=UTC)  # Sunday 6 AM Eastern: the poll run


@pytest.mark.parametrize(
    ("moment", "sunday"),
    [
        (datetime(2026, 11, 8, 11, 0, tzinfo=UTC), date(2026, 11, 8)),  # Sunday morning
        (datetime(2026, 11, 14, 20, 0, tzinfo=UTC), date(2026, 11, 8)),  # Saturday
        (datetime(2026, 11, 8, 3, 0, tzinfo=UTC), date(2026, 11, 1)),  # still Saturday Eastern
        (datetime(2026, 11, 9, 5, 0, tzinfo=UTC), date(2026, 11, 8)),  # Monday 0:00 Eastern
    ],
)
def test_poll_sunday_is_the_latest_eastern_sunday(moment: datetime, sunday: date) -> None:
    assert poll_sunday(moment) == sunday


def test_window_runs_through_the_next_sunday() -> None:
    assert window_end(date(2026, 11, 8)) == datetime(2026, 11, 16, 5, 0, tzinfo=UTC)  # EST


def forecast(
    gid: int, home: int, away: int, margin: float, div: str = "fbs", day: int = 14, away_div=None
):
    kickoff = datetime(2026, 11, day, 20, 0, tzinfo=UTC)
    game = UpcomingGame(gid, 2026, 11, "regular", kickoff, home, away, div, away_div or div, False)
    return GameForecast(game, 3, ScoreDistribution(margin, 55.0, 15.4, 16.4, 0.0))


def ranked(team: int, power: int, resume: int) -> TeamRanking:
    return TeamRanking(team, 0.0, 0.0, 0.0, 9, False, power, None, resume)  # type: ignore[arg-type]


RANKINGS = Rankings(
    season=2026,
    as_of=NOW,
    ratings=None,  # type: ignore[arg-type]  (not read by the picker)
    benchmark=0.0,
    teams=[ranked(1, 1, 9), ranked(2, 2, 8), ranked(3, 3, 1), ranked(4, 30, 2)],
    names={},
    fcs_teams=[ranked(11, 1, 1), ranked(12, 2, 2)],
)


def test_picks_one_game_per_division_and_ranking() -> None:
    games = [
        forecast(100, 1, 2, 1.0),  # #1 vs #2 Power, close
        forecast(101, 3, 4, 0.5),  # #1 vs #2 Résumé, close
        forecast(102, 11, 12, 2.0, "fcs"),
        forecast(103, 1, 11, 0.0, "fbs", away_div="fcs"),  # FBS vs FCS: never picked
    ]
    picks = {
        (p.division, p.ranking_type): p.game_id
        for p in pick_games_of_week(games, RANKINGS, {}, NOW)
    }
    assert picks == {
        ("fbs", "power"): 100,
        ("fbs", "resume"): 101,
        ("fcs", "power"): 102,
        ("fcs", "resume"): 102,
    }


def test_stakes_can_decide_between_similar_games() -> None:
    games = [forecast(100, 1, 2, 1.0), forecast(101, 2, 1, 1.0)]  # identical but for stakes
    big = GameStakes(TeamStakes(0.4, 0.3), TeamStakes(0.5, None))
    (fbs_power, *_) = pick_games_of_week(games, RANKINGS, {101: big}, NOW)
    assert fbs_power.game_id == 101
    assert fbs_power.home_playoff_swing == 0.4 and fbs_power.away_title_swing is None
    assert fbs_power.stakes == pytest.approx((0.55 + 0.5) / 2)


def test_only_games_before_the_end_of_the_next_sunday() -> None:
    late = forecast(100, 1, 2, 0.0, day=17)  # the Tuesday after next Sunday
    assert pick_games_of_week([late], RANKINGS, {}, NOW) == []


def test_a_game_across_divisions_is_never_picked() -> None:
    mixed = forecast(103, 1, 11, 0.0, "fbs", away_div="fcs")
    assert pick_games_of_week([mixed], RANKINGS, {}, NOW) == []
