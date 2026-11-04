"""`fcs_game_missing_stats`: FCS games from 2022 on need advanced stats for both sides."""

from datetime import UTC, datetime

import pytest

from tsi.db.models import Game, Team, TeamGameStats, TeamSeason
from tsi.quality.runner import run_checks

TEAMS = {1: "fbs", 2: "fcs", 3: "fcs", 4: "ii"}


def _game(gid: int, season: int, home: int, away: int) -> Game:
    return Game(
        id=gid,
        season=season,
        week=3,
        season_type="regular",
        start_time=datetime(season, 9, 13, 18, tzinfo=UTC),
        home_id=home,
        away_id=away,
        home_points=28,
        away_points=14,
        completed=True,
    )


def _stats(gid: int, team: int, points: int) -> TeamGameStats:
    return TeamGameStats(game_id=gid, team_id=team, points=points, plays=60, drives=11)


@pytest.mark.db
def test_flags_fcs_games_without_stats_from_2022_only(sessions) -> None:
    with sessions.begin() as s:
        s.add_all([Team(id=t, school=f"T{t}", slug=f"t{t}") for t in TEAMS])
        s.flush()
        s.add_all(
            TeamSeason(team_id=t, season=y, division=d)
            for t, d in TEAMS.items()
            for y in (2021, 2024)
        )
        s.add_all(
            [
                _game(10, 2024, 2, 3),  # FCS vs FCS, no stats: flagged
                _game(11, 2024, 1, 2),  # FBS vs FCS, both sides: fine
                _game(12, 2024, 3, 2),  # FCS vs FCS, one side: flagged
                _game(13, 2021, 2, 3),  # before FCS stats existed: not checked
                _game(14, 2024, 2, 4),  # FCS vs D-II: not rated individually
            ]
        )
        s.flush()
        s.add_all([_stats(11, 1, 28), _stats(11, 2, 14), _stats(12, 3, 28)])

    with sessions() as s:
        (result,) = [r for r in run_checks(s) if r.check.name == "fcs_game_missing_stats"]

    assert (result.check.severity, result.count, result.by_season) == ("warn", 2, {2024: 2})
    assert sorted(e.split("(game ")[1] for e in result.examples) == [
        "10) [no stats]",
        "12) [one side]",
    ]
