import pytest
from tests.model.ratings.test_fit import Row, round_robin

from tsi.model.ratings.components import fit_components


def test_level_is_points_per_game_for_an_average_matchup() -> None:
    # Points = 24 + strength gaps; strengths sum to 0, so the average FBS team scores ~24.
    components = fit_components(round_robin({1: 6, 2: 0, 3: -6}), lam=0.1)

    assert components.ppd.level == pytest.approx(24, abs=0.6)
    assert components.pace.level == pytest.approx(12)  # every row has 12 drives
    assert components.tempo.level == pytest.approx(70)


def test_pace_finds_the_fast_team() -> None:
    # Team 1's games have more drives and plays, whoever it plays.
    rows = []
    for r in round_robin({1: 0, 2: 0, 3: 0}):
        fast = 1 in (r.team_id, r.opp_id)
        rows.append(
            Row(
                r.team_id,
                r.opp_id,
                r.site,
                r.points,
                drives=14 if fast else 11,
                plays=80 if fast else 65,
            )
        )

    components = fit_components(rows, lam=0.1)

    def game_pace(m, a, b):
        ta, tb = m.teams[a], m.teams[b]
        return (ta.off - tb.defense) + (tb.off - ta.defense)

    assert game_pace(components.pace, 1, 2) > game_pace(components.pace, 2, 3)
    assert game_pace(components.tempo, 1, 3) > game_pace(components.tempo, 2, 3)


def test_no_play_counts_means_no_tempo() -> None:
    rows = [
        Row(r.team_id, r.opp_id, r.site, r.points, plays=None) for r in round_robin({1: 3, 2: -3})
    ]

    components = fit_components(rows, lam=1.0)

    assert components.tempo is None and components.success is None
