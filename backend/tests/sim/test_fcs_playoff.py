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


def test_known_games_keep_their_winner_and_real_site() -> None:
    """Once the real bracket is set (#157): a finished upset stands in every simulated
    season, and a scheduled game is played where it really is."""
    from tsi.sim.fcs_playoff import KnownGames

    sims = 4
    field = np.tile(np.arange(24), (sims, 1))
    sim = SimulatedGames(np.zeros((sims, 0)), np.zeros((sims, 24)), 1e-9, np.random.default_rng(0))
    hosts = []

    def margin(a: int, b: int, neutral: bool) -> float:
        hosts.append((a, b, neutral))
        return float(b - a)

    # First round: 16 v 17 (positions -> indexes 15, 16): 17 already won at 16.
    # Second round: 8 hosts the 9/24 winner, but the real game is at 9's stadium (8, 23 -> 8).
    known = KnownGames(winners={(15, 16): 16}, sites={(15, 16): (15, False), (7, 8): (8, False)})
    b = play_fcs_bracket(field, sim, margin, FMT, known)

    assert all(16 in row for row in b.second_round.tolist())  # the upset stands
    assert all(15 not in row for row in b.second_round.tolist())
    assert (8, 7, False) in hosts and (7, 8, False) not in hosts  # 9 hosts 8
    assert b.champion.tolist() == [0] * sims


def test_the_2026_bracket_matches_the_announced_first_round() -> None:
    from tsi.sim.fcs_brackets import FCS_BRACKETS

    bracket = FCS_BRACKETS[2026]
    assert len(set(bracket.field)) == 24
    assert set(bracket.first_round(FMT)) == {
        ("monmouth", "harvard"),
        ("montana", "incarnate-word"),
        ("weber-state", "western-illinois"),
        ("illinois-state", "austin-peay"),
        ("lehigh", "ualbany"),
        ("tennessee-tech", "dayton"),
        ("northern-arizona", "long-island-university"),
        ("north-dakota", "idaho-state"),
    }
    # Bye seed s meets the winner of the game at seed 17 - s (1 v 16/17, ..., 8 v 9/24).
    second = {bracket.field[s - 1]: bracket.field[8 + g] for s, g in FMT.second_round}
    assert second["montana-state"] == "monmouth" and second["mercer"] == "north-dakota"
    assert second["lamar"] == "illinois-state" and second["tarleton-state"] == "montana"
