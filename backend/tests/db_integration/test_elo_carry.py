"""Live runs resume Elo from the saved state only while the games still match (#146)."""

from datetime import UTC, datetime

import pytest

from tsi.db.models import Game, Team, TeamSeason
from tsi.db.queries.results import completed_games, completed_games_fingerprint
from tsi.model.elo import EloParams, run_elo
from tsi.services.elo_carry import build_elo_carry, starting_elo

GAMES = [  # id, season, month, home, away, home points, away points
    (1, 2024, 9, 1, 2, 30, 20),
    (2, 2024, 10, 2, 3, 14, 17),
    (3, 2025, 9, 3, 1, 21, 24),
    (4, 2026, 9, 1, 3, 35, 7),
]


def seed(sessions) -> None:
    with sessions.begin() as s:
        s.add_all([Team(id=t, school=f"T{t}", slug=f"t{t}") for t in (1, 2, 3)])
        s.flush()
        s.add_all(
            TeamSeason(team_id=t, season=y, division="fcs" if t == 3 else "fbs", conference="C")
            for t in (1, 2, 3)
            for y in (2024, 2025, 2026)
        )
        s.add_all(
            Game(
                id=g,
                season=y,
                week=1,
                season_type="regular",
                start_time=datetime(y, m, 1, 18, tzinfo=UTC),
                home_id=h,
                away_id=a,
                home_points=hp,
                away_points=ap,
                completed=True,
            )
            for g, y, m, h, a, hp, ap in GAMES
        )


@pytest.mark.db
def test_resumed_elo_matches_a_full_replay(sessions) -> None:
    seed(sessions)
    params = EloParams()
    with sessions() as s:
        carry = build_elo_carry(s, 2025, params)
        start = starting_elo(s, 2026, params, carry)
        assert start is not None
        resumed = run_elo(completed_games(s, 2026, from_season=2026), params, start)
        whole = run_elo(completed_games(s, 2026), params)
    assert resumed.ratings == whole.ratings
    assert resumed.divisions == whole.divisions


@pytest.mark.db
def test_any_change_to_past_games_falls_back_to_a_full_replay(sessions) -> None:
    seed(sessions)
    params = EloParams()
    with sessions() as s:
        carry = build_elo_carry(s, 2025, params)
        before = completed_games_fingerprint(s, 2025)
    assert carry.fingerprint == before

    with sessions.begin() as s:
        s.get(Game, 2).away_points = 18  # a corrected score
    with sessions() as s:
        assert completed_games_fingerprint(s, 2025) != before
        assert starting_elo(s, 2026, params, carry) is None
        assert completed_games_fingerprint(s, 2026) != completed_games_fingerprint(s, 2025)

    with sessions.begin() as s:
        s.get(Game, 2).away_points = 17
        s.get(TeamSeason, (2, 2024)).division = "fcs"  # a division changes the replay too
    with sessions() as s:
        assert starting_elo(s, 2026, params, carry) is None
