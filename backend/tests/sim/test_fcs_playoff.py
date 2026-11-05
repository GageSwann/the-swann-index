import numpy as np

from tsi.sim.fcs_format import FCS_FORMAT_2026 as FMT
from tsi.sim.fcs_playoff import fcs_field, play_fcs_bracket
from tsi.sim.season import SimulatedGames

N = 30  # teams 0..29, ranked in index order


def order(sims: int = 1) -> np.ndarray:
    return np.tile(np.arange(N), (sims, 1))


def test_auto_bids_then_at_large_by_rank_skipping_ineligible_teams() -> None:
    eligible = np.ones(N, dtype=bool)
    eligible[[2, 5]] = False  # e.g. moving up from Division II
    bids = np.array([[27, 29, -1]])  # two low-ranked champions; one conference has no bid

    field = fcs_field(order(), bids, eligible, FMT)

    expected = [t for t in range(N) if t not in (2, 5)][:22] + [27, 29]
    assert field.tolist() == [sorted(expected)]
    assert field[0, :8].tolist() == [0, 1, 3, 4, 6, 7, 8, 9]  # the seeds


def test_too_few_eligible_teams_gives_no_field() -> None:
    eligible = np.arange(N) < 20

    assert fcs_field(order(), np.full((1, 1), -1), eligible, FMT) is None


def test_bracket_without_noise_follows_the_means() -> None:
    sims = 3
    field = np.tile(np.arange(24), (sims, 1))
    sim = SimulatedGames(np.zeros((sims, 0)), np.zeros((sims, 24)), 1e-9, np.random.default_rng(0))
    hosts = []

    def margin(a: int, b: int, neutral: bool) -> float:
        hosts.append((a, neutral))
        return float(b - a)  # the lower index is always better

    b = play_fcs_bracket(field, sim, margin, FMT)

    assert b.champion.tolist() == [0] * sims
    assert sorted(b.quarterfinalists[0].tolist()) == list(range(8))  # seeds win at home
    assert sorted(b.semifinalists[0].tolist()) == [0, 1, 2, 3]
    assert sorted(b.finalists[0].tolist()) == [0, 1]
    assert b.second_round.shape == (sims, 16)
    assert hosts[-1][1] and not any(n for _, n in hosts[:-1])  # only the final is neutral
    assert all(h in range(16) for h, _ in hosts[:8])  # first round: the better team hosts


def test_format_pairs_every_position_once() -> None:
    first = [p for game in FMT.first_round for p in game]
    assert sorted(first) == list(range(9, 25))
    assert sorted(s for s, _ in FMT.second_round) == list(range(1, 9))
    assert sorted(g for _, g in FMT.second_round) == list(range(8))
    assert sorted(i for q in FMT.quarterfinals for i in q) == list(range(8))
