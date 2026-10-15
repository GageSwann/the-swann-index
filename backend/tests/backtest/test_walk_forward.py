"""Walk-forward must never use a game's own result (or later ones) to predict it."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from tsi.backtest.walk_forward import refit_day, walk_forward
from tsi.db.queries.results import GameResult
from tsi.db.queries.stats import OffenseRow

SAT = datetime(2024, 9, 7, 19, 0, tzinfo=UTC)


def game(gid, home, away, hp, ap, when):
    return GameResult(gid, 2024, when, home, away, "fbs", "fbs", False, hp, ap)


def rows_for(g: GameResult) -> list[OffenseRow]:
    common = dict(
        game_id=g.id,
        season=2024,
        start_time=g.start_time,
        team_div="fbs",
        opp_div="fbs",
        drives=12,
        plays=70,
        epa_per_play=0.1,
    )
    return [
        OffenseRow(team_id=g.home_id, opp_id=g.away_id, site=1, points=g.home_points, **common),
        OffenseRow(team_id=g.away_id, opp_id=g.home_id, site=-1, points=g.away_points, **common),
    ]


def run(games):
    rows = {2024: [r for g in games for r in rows_for(g)]}
    return walk_forward(games, rows, priors={}, prior_hfa=0.0)


def test_refit_day_uses_the_10am_utc_run() -> None:
    late_saturday_game = datetime(2024, 9, 8, 3, 30, tzinfo=UTC)  # 11:30pm ET Saturday
    assert refit_day(late_saturday_game) == datetime(2024, 9, 7).date()


def test_predictions_ignore_their_own_and_later_results() -> None:
    games = [
        game(1, 1, 2, 30, 10, SAT),
        game(2, 3, 4, 24, 21, SAT),
        game(3, 1, 3, 20, 17, SAT + timedelta(days=7)),
        game(4, 2, 4, 35, 0, SAT + timedelta(days=14)),
    ]
    changed = games[:2] + [replace(games[2], home_points=0, away_points=63), games[3]]

    base, alt = run(games), run(changed)

    for i in range(3):  # games 1-3 are predicted before game 3's result exists
        assert base[i].season_margin == alt[i].season_margin
    assert base[3].season_margin != alt[3].season_margin  # game 4 sees game 3's result


def test_first_week_has_no_information() -> None:
    picks = run([game(1, 1, 2, 30, 10, SAT)])

    assert picks[0].season_margin == 0.0 and picks[0].established is False
