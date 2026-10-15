from dataclasses import dataclass, replace

import pytest

from tsi.model.elo import (
    EloParams,
    fit_points_per_elo,
    home_win_prob,
    margin_multiplier,
    run_elo,
)


@dataclass(frozen=True)
class G:
    id: int
    season: int
    home_id: int
    away_id: int
    home_points: int
    away_points: int
    neutral: bool = False
    home_div: str = "fbs"
    away_div: str = "fbs"


def test_equal_teams_neutral_site_is_a_coin_flip() -> None:
    assert home_win_prob(0) == pytest.approx(0.5)
    assert home_win_prob(400) == pytest.approx(10 / 11)


def test_first_game_uses_division_means_and_home_field() -> None:
    run = run_elo([G(1, 2024, 1, 2, 30, 20)])

    pred = run.predictions[0]
    assert pred.elo_diff == pytest.approx(EloParams().hfa)
    assert pred.home_win_prob > 0.5


def test_neutral_site_has_no_home_field() -> None:
    assert run_elo([G(1, 2024, 1, 2, 30, 20, neutral=True)]).predictions[0].elo_diff == 0


def test_updates_are_zero_sum_and_reward_the_winner() -> None:
    ratings = run_elo([G(1, 2024, 1, 2, 10, 35)]).ratings

    assert ratings[2] > 1500 > ratings[1]
    assert ratings[1] + ratings[2] == pytest.approx(3000)


def test_bigger_margins_move_ratings_more() -> None:
    close = run_elo([G(1, 2024, 1, 2, 21, 20)]).ratings[1]
    blowout = run_elo([G(1, 2024, 1, 2, 56, 0)]).ratings[1]

    assert blowout > close > 1500


def test_heavy_favorite_blowout_counts_less_than_upset_blowout() -> None:
    assert margin_multiplier(28, winner_elo_diff=300) < margin_multiplier(28, winner_elo_diff=-300)


def test_division_means_seed_new_teams() -> None:
    pred = run_elo([G(1, 2024, 1, 2, 49, 7, away_div="fcs")]).predictions[0]

    assert pred.elo_diff == pytest.approx(1500 - 1300 + EloParams().hfa)


def test_ratings_regress_toward_mean_between_seasons() -> None:
    blowout_2023 = G(1, 2023, 1, 2, 63, 0)
    after_2023 = run_elo([blowout_2023]).ratings[1]
    # Team 1's first 2024 game is vs. a brand-new team (1500) at a neutral site,
    # so its pre-game Elo difference equals its regressed rating minus 1500.
    first_2024 = G(2, 2024, 1, 99, 0, 0, neutral=True)

    pred = run_elo([blowout_2023, first_2024]).predictions[1]

    regressed = 1500 + EloParams().carryover * (after_2023 - 1500)
    assert pred.elo_diff == pytest.approx(regressed - 1500)
    assert 0 < pred.elo_diff < after_2023 - 1500


def test_no_look_ahead_predictions_ignore_their_own_and_later_results() -> None:
    games = [G(1, 2024, 1, 2, 24, 21), G(2, 2024, 1, 3, 10, 0), G(3, 2024, 2, 3, 31, 3)]
    changed = [games[0], replace(games[1], home_points=0, away_points=70), games[2]]

    base, alt = run_elo(games).predictions, run_elo(changed).predictions

    assert base[0] == alt[0] and base[1] == alt[1]  # game 2's result can't affect games 1-2
    assert base[2] != alt[2]  # but it does affect the later game


def test_fit_points_per_elo_recovers_the_slope() -> None:
    diffs = [50.0, -100.0, 200.0]

    assert fit_points_per_elo(diffs, [d / 20 for d in diffs]) == pytest.approx(20)
    with pytest.raises(ValueError):
        fit_points_per_elo(diffs, [-d for d in diffs])
