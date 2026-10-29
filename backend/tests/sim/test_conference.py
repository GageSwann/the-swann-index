import numpy as np
import pytest

from tsi.sim.conference import Conference, simulate_title, title_odds
from tsi.sim.season import SimulatedGames
from tsi.sim.standings import ConferenceGame, head_to_head, rank


def sim_of(margins: list[list[float]], n_teams: int, noise: float = 1e-6) -> SimulatedGames:
    m = np.array(margins, dtype=float)
    return SimulatedGames(m, np.zeros((m.shape[0], n_teams)), noise, np.random.default_rng(0))


def finished(home: int, away: int, home_won: bool) -> ConferenceGame:
    return ConferenceGame(home, away, home_won=home_won)


def test_rank_orders_by_win_percentage() -> None:
    games = [finished(0, 1, True), finished(0, 2, True), finished(1, 2, True)]
    wins = head_to_head(games, np.zeros((1, 0), dtype=bool), 3)

    assert rank(wins, np.zeros((1, 3)), np.arange(3)).tolist() == [[0, 1, 2]]


def test_tie_goes_to_head_to_head_then_rating() -> None:
    # 0, 1, 2 each 1-1 in a cycle (no head-to-head edge); 3 lost to all three.
    games = [finished(0, 1, True), finished(1, 2, True), finished(2, 0, True)]
    games += [finished(t, 3, True) for t in (0, 1, 2)]
    wins = head_to_head(games, np.zeros((1, 0), dtype=bool), 4)
    strength = np.array([[0.0, 5.0, 1.0, 9.0]])

    assert rank(wins, strength, np.arange(4)).tolist() == [[1, 2, 0, 3]]  # cycle -> rating

    # Two-way tie: 0 and 1 both 2-1, 0 beat 1 -> 0 first despite the lower rating.
    games = [finished(0, 1, True), finished(2, 0, True), finished(1, 2, True)]
    games += [finished(t, 3, True) for t in (0, 1)] + [finished(3, 2, True)]
    wins = head_to_head(games, np.zeros((1, 0), dtype=bool), 4)
    assert rank(wins, strength, np.arange(4))[0, :2].tolist() == [0, 1]


def test_top_two_meet_and_the_better_team_wins_without_noise() -> None:
    games = (finished(0, 1, True), finished(0, 2, True), finished(1, 2, True))
    neutral = np.array([[0, 3, 10], [-3, 0, 7], [-10, -7, 0]], dtype=float)
    conf = Conference("C", (10, 11, 12), games, neutral)

    res = simulate_title(conf, sim_of([[0.0]] * 4, n_teams=13))

    assert res.added_game
    assert res.finalists.tolist() == [[10, 11]] * 4
    assert res.champion.tolist() == [10] * 4


def test_divisions_send_each_winner() -> None:
    games = (finished(0, 1, True), finished(2, 3, True), finished(1, 3, True))
    neutral = np.zeros((4, 4))
    conf = Conference("C", (0, 1, 2, 3), games, neutral, divisions=((0, 1), (2, 3)))

    res = simulate_title(conf, sim_of([[0.0]], n_teams=4))

    assert sorted(res.finalists[0].tolist()) == [0, 2]  # 1 is 1-1, second in the standings


def test_a_scheduled_title_game_decides_the_champion() -> None:
    title = ConferenceGame(1, 2, column=0)
    conf = Conference("C", (5, 6, 7), (), np.zeros((3, 3)), title_game=title)

    res = simulate_title(conf, sim_of([[4.0], [-4.0]], n_teams=8))

    assert not res.added_game
    assert res.finalists.tolist() == [[6, 7], [6, 7]]
    assert res.champion.tolist() == [6, 7]


def test_title_odds_add_up() -> None:
    games = (finished(0, 1, True),)
    conf = Conference("C", (0, 1, 2), games, np.zeros((3, 3)))
    sim = SimulatedGames(np.zeros((5000, 0)), np.random.default_rng(1).normal(0, 6, (5000, 3)),
                         15.0, np.random.default_rng(2))  # fmt: skip

    odds = title_odds(simulate_title(conf, sim), [0, 1, 2])

    assert sum(f for f, _ in odds.values()) == pytest.approx(2.0)
    assert sum(c for _, c in odds.values()) == pytest.approx(1.0)
    assert odds[0][1] > odds[2][1]
