"""The Résumé ranking at the end of every simulated season (the committee stand-in, #100).

SOR = P(a typical #12 team, playing the same schedule, wins at least as many games)
(model/resume.py). For a fixed schedule it depends only on the win count, so each team
gets a lookup table over its full regular season: tail[k] = P(benchmark wins >= k).
A conference title game adds one game against that simulation's opponent:
P(B_{n+1} >= k) = tail[k] + p * (tail[k-1] - tail[k]). Opponents keep today's ratings.
"""

from collections.abc import Sequence

import numpy as np

from tsi.model.resume import poisson_binomial


def sor_table(benchmark_win_probs: Sequence[float]) -> np.ndarray:
    """tail[k] = P(benchmark wins >= k), k = 0 .. n+1 (the last entry is 0)."""
    dist = poisson_binomial(benchmark_win_probs)
    tail = np.cumsum(dist[::-1])[::-1]
    return np.append(tail, 0.0)


def simulated_sor(
    tables: Sequence[np.ndarray],
    wins: np.ndarray,  # (sims, teams) final wins, title game included
    title_game_p: np.ndarray,  # (sims, teams) benchmark's chance in the title game; NaN: none
) -> np.ndarray:
    """(sims, teams) SOR for each team's simulated final record."""
    sor = np.empty(wins.shape)
    for t, tail in enumerate(tables):
        top = len(tail) - 1
        k = np.clip(wins[:, t], 0, top)
        at_k = tail[k]
        below = tail[np.clip(k - 1, 0, top)]
        p = title_game_p[:, t]
        sor[:, t] = np.where(np.isnan(p), at_k, at_k + np.nan_to_num(p) * (below - at_k))
    return sor


def resume_order(sor: np.ndarray, wins: np.ndarray, rating: np.ndarray) -> np.ndarray:
    """(sims, teams) team indexes best first: lowest SOR, then more wins, then rating
    (the stored ranking's order, services/compute_rankings.py)."""
    ratings = np.broadcast_to(rating, sor.shape)
    return np.lexsort((-ratings, -wins, sor), axis=-1)
