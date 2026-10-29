import math

import numpy as np
import pytest

from tsi.model.ratings.probability import win_prob
from tsi.sim.season import RemainingGame, simulate_games, wins_added
from tsi.sim.uncertainty import LAST_WEEK, game_noise, rating_tau

SIGMA = 15.4


def test_tau_shrinks_through_the_season_and_holds_after_it() -> None:
    assert rating_tau(0) == pytest.approx(7.15)
    assert rating_tau(9) < rating_tau(4) < rating_tau(0)
    assert rating_tau(LAST_WEEK + 5) == rating_tau(LAST_WEEK)
    assert rating_tau(-1) == rating_tau(0)


def test_noise_keeps_each_games_total_sigma() -> None:
    tau = rating_tau(4)
    assert math.hypot(game_noise(SIGMA, tau), tau, tau) == pytest.approx(SIGMA)


def test_single_game_win_probabilities_match_the_published_ones() -> None:
    games = [RemainingGame(0, 1, -7.0), RemainingGame(2, 3, 3.5)]
    tau = rating_tau(4)
    sim = simulate_games(games, 4, tau, game_noise(SIGMA, tau), sims=200_000)

    p = sim.home_wins.mean(axis=0)
    assert p[0] == pytest.approx(win_prob(-7.0, SIGMA), abs=0.005)
    assert p[1] == pytest.approx(win_prob(3.5, SIGMA), abs=0.005)


def test_rating_uncertainty_ties_a_teams_games_together() -> None:
    games = [RemainingGame(0, 1, 0.0), RemainingGame(0, 2, 0.0)]  # team 0 home twice

    def correlation(tau: float) -> float:
        won = simulate_games(games, 3, tau, game_noise(SIGMA, tau), sims=100_000).home_wins
        return float(np.corrcoef(won[:, 0], won[:, 1])[0, 1])

    assert abs(correlation(0.0)) < 0.02
    assert correlation(rating_tau(0)) > 0.1


def test_wins_are_credited_to_the_winner() -> None:
    games = [RemainingGame(0, 1, 500.0), RemainingGame(2, 0, 500.0), RemainingGame(1, 2, -500.0)]
    sim = simulate_games(games, 3, tau=1.0, noise=1.0, sims=10)

    wins = wins_added(sim, games, 3)
    assert wins.tolist() == [[1, 0, 2]] * 10  # 0 beat 1, 2 beat 0, 2 beat 1 on the road


def test_same_seed_same_simulation() -> None:
    games = [RemainingGame(0, 1, 1.0)]
    a = simulate_games(games, 2, 5.0, 14.0, sims=1000)
    b = simulate_games(games, 2, 5.0, 14.0, sims=1000)
    assert np.array_equal(a.margins, b.margins)
