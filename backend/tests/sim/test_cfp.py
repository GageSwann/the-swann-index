import numpy as np
import pytest

from tsi.model.resume import poisson_binomial
from tsi.sim.bracket import play_bracket
from tsi.sim.cfp import FieldInputs, seeds
from tsi.sim.cfp_format import FORMAT_2026
from tsi.sim.resume_sim import resume_order, simulated_sor, sor_table
from tsi.sim.season import SimulatedGames

PROBS = [0.9, 0.6, 0.3]


def test_sor_table_matches_the_stored_definition() -> None:
    tail = sor_table(PROBS)
    dist = poisson_binomial(PROBS)

    for k in range(4):
        assert tail[k] == pytest.approx(sum(dist[k:]))  # P(benchmark wins >= k)
    assert tail[4] == 0.0 and tail[0] == pytest.approx(1.0)


def test_a_title_game_adds_one_game_to_the_schedule() -> None:
    tables = [sor_table(PROBS)]
    wins = np.array([[3], [2], [0]])
    p = np.array([[0.4], [0.4], [np.nan]])

    sor = simulated_sor(tables, wins, p)

    with_title = poisson_binomial([*PROBS, 0.4])
    assert sor[0, 0] == pytest.approx(sum(with_title[3:]))
    assert sor[1, 0] == pytest.approx(sum(with_title[2:]))
    assert sor[2, 0] == pytest.approx(1.0)  # no title game; 0 wins


def test_resume_order_breaks_ties_by_wins_then_rating() -> None:
    sor = np.array([[0.2, 0.2, 0.1, 0.2]])
    wins = np.array([[9, 10, 8, 10]])
    rating = np.array([5.0, 1.0, 0.0, 3.0])

    assert resume_order(sor, wins, rating).tolist() == [[2, 3, 1, 0]]


def ranked_field(order: list[int], champions: list[int], group: set[int], independent=None):
    members = np.array([t in group for t in range(len(order))])
    inputs = FieldInputs(np.array([champions]), members, independent)
    return seeds(np.array([order]), inputs, FORMAT_2026)[0].tolist()


def test_automatic_bids_bump_the_last_at_large_teams() -> None:
    order = list(range(20))  # team t is ranked t + 1
    # Champions ranked 2, 3, 15 and 16; the best group-conference team is ranked 18.
    field = ranked_field(order, [1, 2, 14, 15], group={17, 19})

    # 5 automatic bids + the 7 best-ranked others, seeded by rank.
    assert field == [0, 1, 2, 3, 4, 5, 6, 7, 8, 14, 15, 17]


def test_the_independent_needs_a_top_12_ranking() -> None:
    order = list(range(20))
    in_at_12 = ranked_field(order, [0, 1, 2, 3], group={19}, independent=11)
    out_at_13 = ranked_field(order, [0, 1, 2, 3], group={19}, independent=12)

    assert 11 in in_at_12
    assert 12 not in out_at_13 and out_at_13[-1] == 19  # group bid takes the last spot


def test_bracket_pairings_follow_the_seeds() -> None:
    field = np.array([list(range(12))])  # team i is seed i + 1
    sim = SimulatedGames(np.zeros((1, 0)), np.zeros((1, 12)), 1e-9, np.random.default_rng(0))
    pairs = []

    def mean(a: int, b: int, neutral: bool) -> float:
        pairs.append((a + 1, b + 1, neutral))  # as seeds
        return 1.0  # the first-listed team always wins

    res = play_bracket(field, sim, mean, FORMAT_2026)

    first = [(5, 12, False), (6, 11, False), (7, 10, False), (8, 9, False)]
    quarters = [(1, 8, True), (2, 7, True), (3, 6, True), (4, 5, True)]
    assert pairs[:8] == first + quarters
    assert pairs[8:] == [(1, 4, True), (2, 3, True), (1, 2, True)]
    assert res.champion.tolist() == [0]
    assert sorted(res.semifinalists[0].tolist()) == [0, 1, 2, 3]
