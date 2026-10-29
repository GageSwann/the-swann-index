"""Play the playoff bracket in every simulated season.

Game means come from the published model (the caller's `mean_margin`, cached per pairing):
first-round games at the higher seed's home, everything after at neutral sites. Each
game adds both teams' rating shifts from the same simulation and fresh game noise.
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from tsi.sim.cfp_format import CfpFormat
from tsi.sim.season import SimulatedGames

MeanMargin = Callable[[int, int, bool], float]  # (team a, team b, neutral) -> a's margin


@dataclass(frozen=True)
class BracketResults:
    seeds: np.ndarray  # (sims, field) team index per seed
    quarterfinalists: np.ndarray  # (sims, 8)
    semifinalists: np.ndarray  # (sims, 4)
    finalists: np.ndarray  # (sims, 2)
    champion: np.ndarray  # (sims,)


def play_bracket(
    seeds: np.ndarray, sim: SimulatedGames, mean_margin: MeanMargin, fmt: CfpFormat
) -> BracketResults:
    cache: dict[tuple[int, int, bool], float] = {}

    def play(a: np.ndarray, b: np.ndarray, neutral: bool) -> np.ndarray:
        pairs = zip(a.tolist(), b.tolist(), strict=True)
        means = np.array([_mean(cache, mean_margin, x, y, neutral) for x, y in pairs])
        rows = np.arange(len(a))
        margin = means + sim.shift[rows, a] - sim.shift[rows, b]
        margin += sim.rng.normal(0.0, sim.noise, len(a))
        return np.where(margin > 0, a, b)

    seed = lambda s: seeds[:, s - 1]  # noqa: E731 (seed number -> team column)
    first = [play(seed(hi), seed(lo), neutral=False) for hi, lo in fmt.first_round]
    quarter_teams = [(seed(bye), first[game]) for bye, game in fmt.quarterfinals]
    quarters = [play(a, b, neutral=True) for a, b in quarter_teams]
    semis = [play(quarters[i], quarters[j], neutral=True) for i, j in fmt.semifinals]
    champion = play(semis[0], semis[1], neutral=True)
    return BracketResults(
        seeds=seeds,
        quarterfinalists=np.stack([t for pair in quarter_teams for t in pair], axis=1),
        semifinalists=np.stack(quarters, axis=1),
        finalists=np.stack(semis, axis=1),
        champion=champion,
    )


def _mean(cache, mean_margin: MeanMargin, a: int, b: int, neutral: bool) -> float:
    key = (a, b, neutral)
    if key not in cache:
        cache[key] = mean_margin(a, b, neutral)
    return cache[key]
