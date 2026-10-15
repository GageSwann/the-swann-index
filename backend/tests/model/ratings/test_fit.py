from dataclasses import dataclass

import pytest

from tsi.model.ratings.design import POOLED_ID, build_design, involves_rated_team
from tsi.model.ratings.fit import AVERAGE, RatingParams, fit_ratings, predicted_margin
from tsi.model.ratings.probability import residual_sigma, win_prob


@dataclass(frozen=True)
class Row:
    team_id: int
    opp_id: int
    site: int
    points: int
    drives: int | None = 12
    plays: int | None = 70
    epa_per_play: float | None = 0.1
    team_div: str = "fbs"
    opp_div: str = "fbs"


def game(home, away, home_pts, away_pts, neutral=False, **kw):
    s = 0 if neutral else 1
    return [Row(home, away, s, home_pts, **kw), Row(away, home, -s, away_pts, **kw)]


def round_robin(strength: dict[int, float], rounds: int = 3) -> list[Row]:
    """Each pair plays home-and-away; points = 24 + own strength - opponent's."""
    rows = []
    teams = sorted(strength)
    for _ in range(rounds):
        for a in teams:
            for b in teams:
                if a < b:
                    for home, away in ((a, b), (b, a)):
                        hp = round(24 + strength[home] - strength[away] / 2 + 1.5)
                        ap = round(24 + strength[away] - strength[home] / 2 - 1.5)
                        rows += game(home, away, hp, ap)
    return rows


def test_recovers_team_order_and_centers_fbs_average_on_zero() -> None:
    ratings = fit_ratings(round_robin({1: 10, 2: 3, 3: -2, 4: -11}), RatingParams(lam=0.1))

    order = sorted(ratings.teams, key=lambda t: ratings.teams[t].rating, reverse=True)
    assert order == [1, 2, 3, 4]
    assert sum(t.rating for t in ratings.teams.values()) == pytest.approx(0, abs=1e-6)
    assert ratings.hfa > 0


def test_stronger_penalty_compresses_ratings() -> None:
    rows = round_robin({1: 10, 2: 3, 3: -2, 4: -11})
    loose = fit_ratings(rows, RatingParams(lam=0.1)).teams[1].rating
    tight = fit_ratings(rows, RatingParams(lam=50)).teams[1].rating

    assert 0 < tight < loose


def test_non_fbs_teams_are_pooled_and_fcs_only_games_dropped() -> None:
    fbs_vs_fcs = [
        Row(1, 900, 1, 49, opp_div="fcs"),
        Row(900, 1, -1, 7, team_div="fcs"),
        Row(1, 901, 1, 56, opp_div="ii"),
        Row(901, 1, -1, 3, team_div="ii"),
    ]
    fcs_only = [
        Row(900, 901, 1, 21, team_div="fcs", opp_div="ii"),
        Row(901, 900, -1, 20, team_div="ii", opp_div="fcs"),
    ]

    assert all(involves_rated_team(r) for r in fbs_vs_fcs)
    assert not any(involves_rated_team(r) for r in fcs_only)
    assert set(build_design(fbs_vs_fcs).team_index) == {1, POOLED_ID}


def test_missing_epa_falls_back_to_points_per_drive() -> None:
    rows = round_robin({1: 8, 2: -8})
    no_epa = [Row(r.team_id, r.opp_id, r.site, r.points, epa_per_play=None) for r in rows]

    ratings = fit_ratings(no_epa)

    assert ratings.teams[1].rating > ratings.teams[2].rating


def test_no_games_means_everyone_is_average() -> None:
    assert fit_ratings([]) is AVERAGE
    assert AVERAGE.get(123, "fbs").rating == 0


def test_all_neutral_site_games_fit_without_home_field() -> None:
    rows = game(1, 2, 35, 10, neutral=True) + game(3, 4, 20, 17, neutral=True)

    assert fit_ratings(rows).hfa == pytest.approx(0, abs=1e-6)


def test_predicted_margin_is_antisymmetric_at_neutral_site() -> None:
    ratings = fit_ratings(round_robin({1: 10, 2: -10}))
    a, b = ratings.teams[1], ratings.teams[2]

    assert predicted_margin(ratings, a, b, neutral=True) == pytest.approx(
        -predicted_margin(ratings, b, a, neutral=True)
    )
    assert predicted_margin(ratings, a, b, neutral=False) == pytest.approx(
        predicted_margin(ratings, a, b, neutral=True) + ratings.hfa
    )


def test_win_probability_and_sigma() -> None:
    assert win_prob(0, 15) == pytest.approx(0.5)
    assert win_prob(15, 15) == pytest.approx(0.8413, abs=1e-4)
    assert residual_sigma([0, 0, 0, 0], [1, -1, 1, -1]) == pytest.approx(2 / 3**0.5)
