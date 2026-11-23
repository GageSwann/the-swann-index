"""Live runs take last season's fit from the saved carry only while the stats still match."""

from datetime import UTC, datetime

import pytest

from tsi.db.models import Game, Team, TeamGameStats, TeamSeason
from tsi.db.queries.stats import offense_rows, offense_rows_fingerprint
from tsi.model.ratings.components import fit_components
from tsi.services.component_carry import build_component_carry, last_season_components

TEAMS = (1, 2, 3, 4)
LAM, VERSION = 2.0, "tsi-v1.7"


def seed(sessions) -> None:
    """A round robin per season, every pairing home and away, with uneven stats."""
    games = [
        (gid, season, h, a)
        for gid, (season, h, a) in enumerate(
            ((s, h, a) for s in (2025, 2026) for h in TEAMS for a in TEAMS if h != a), start=1
        )
    ]
    with sessions.begin() as s:
        s.add_all([Team(id=t, school=f"T{t}", slug=f"t{t}") for t in TEAMS])
        s.flush()
        s.add_all(
            TeamSeason(team_id=t, season=y, division="fcs" if t == 4 else "fbs", conference="C")
            for t in TEAMS
            for y in (2025, 2026)
        )
        s.add_all(
            Game(
                id=g,
                season=y,
                week=1,
                season_type="regular",
                start_time=datetime(y, 9, 1 + g % 28, 18, tzinfo=UTC),
                home_id=h,
                away_id=a,
                home_points=20 + 3 * h,
                away_points=10 + 2 * a,
                completed=True,
            )
            for g, y, h, a in games
        )
        s.flush()
        s.add_all(
            TeamGameStats(
                game_id=g,
                team_id=t,
                points=(20 + 3 * h) if t == h else (10 + 2 * a),
                drives=11 + (g + t) % 3,
                plays=60 + (g * t) % 15,
                epa_per_play=0.01 * t,
                success_rate=0.35 + 0.01 * ((g + 2 * t) % 7),
                second_level_yards=0.5 + 0.1 * t,
                power_success=None if g % 5 == 0 else 0.6,
            )
            for g, _, h, a in games
            for t in (h, a)
        )


@pytest.mark.db
def test_saved_fit_matches_a_fresh_fit(sessions) -> None:
    seed(sessions)
    with sessions() as s:
        carry = build_component_carry(s, 2025, LAM, VERSION)
        assert carry is not None
        fresh = fit_components(offense_rows(s, 2025, 2025), LAM)
        used = last_season_components(s, 2026, LAM, VERSION, carry)
    assert used is carry.components
    assert repr(used) == repr(fresh)


@pytest.mark.db
def test_any_change_to_last_seasons_stats_fits_again(sessions) -> None:
    seed(sessions)
    with sessions() as s:
        carry = build_component_carry(s, 2025, LAM, VERSION)
        before = offense_rows_fingerprint(s, 2025)
        this_season = offense_rows_fingerprint(s, 2026)
    assert carry is not None and carry.fingerprint == before != this_season

    with sessions.begin() as s:
        s.get(TeamGameStats, (2, 1)).success_rate = 0.4123  # a CFBD correction
    with sessions() as s:
        assert offense_rows_fingerprint(s, 2025) != before
        refit = last_season_components(s, 2026, LAM, VERSION, carry)
        assert refit is not carry.components
        assert repr(refit) == repr(fit_components(offense_rows(s, 2025, 2025), LAM))


@pytest.mark.db
def test_fingerprint_tells_a_missing_value_from_a_moved_one(sessions) -> None:
    """concat_ws drops NULLs, so without a marker these two rows would print the same."""
    seed(sessions)
    with sessions.begin() as s:
        row = s.get(TeamGameStats, (1, 1))
        row.second_level_yards, row.power_success = None, 0.6
    with sessions() as s:
        first = offense_rows_fingerprint(s, 2025)
    with sessions.begin() as s:
        row = s.get(TeamGameStats, (1, 1))
        row.second_level_yards, row.power_success = 0.6, None
    with sessions() as s:
        assert offense_rows_fingerprint(s, 2025) != first


@pytest.mark.db
def test_other_seasons_or_fits_never_use_the_carry(sessions) -> None:
    seed(sessions)
    with sessions() as s:
        carry = build_component_carry(s, 2025, LAM, VERSION)
        assert last_season_components(s, 2027, LAM, VERSION, carry) is not carry.components
        assert last_season_components(s, 2026, 3.0, VERSION, carry) is not carry.components
        assert last_season_components(s, 2026, LAM, "tsi-v1.8", carry) is not carry.components
        assert build_component_carry(s, 2024, LAM, VERSION) is None  # no stats that season
