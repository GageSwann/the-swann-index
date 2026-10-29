"""Monte Carlo of the rest of a season: who wins each remaining game, in every simulation.

Inputs are plain arrays: the remaining games' mean home margins (the published
forecasts) and team indexes. Each simulation draws one rating shift per team
(sim/uncertainty.py) and then every game's margin. Finished games aren't simulated;
the caller adds their results.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

DEFAULT_SIMS = 10_000
DEFAULT_SEED = 2026  # fixed: the same inputs give the same projections


@dataclass(frozen=True)
class RemainingGame:
    home: int  # team index into the simulation's team list
    away: int
    mean_margin: float  # home view, from the published forecast


@dataclass(frozen=True)
class SimulatedGames:
    margins: np.ndarray  # (sims, games) home-view margins

    @property
    def home_wins(self) -> np.ndarray:
        return self.margins > 0


def simulate_games(
    games: Sequence[RemainingGame],
    n_teams: int,
    tau: float,
    noise: float,
    sims: int = DEFAULT_SIMS,
    seed: int = DEFAULT_SEED,
) -> SimulatedGames:
    """Margins of every remaining game in every simulated season."""
    rng = np.random.default_rng(seed)
    shift = rng.normal(0.0, tau, size=(sims, n_teams))
    home = np.array([g.home for g in games], dtype=int)
    away = np.array([g.away for g in games], dtype=int)
    mean = np.array([g.mean_margin for g in games], dtype=float)
    margins = mean + shift[:, home] - shift[:, away] + rng.normal(0.0, noise, (sims, len(games)))
    return SimulatedGames(margins)


def wins_added(sim: SimulatedGames, games: Sequence[RemainingGame], n_teams: int) -> np.ndarray:
    """(sims, teams): wins each team adds over the remaining games."""
    home = np.array([g.home for g in games], dtype=int)
    away = np.array([g.away for g in games], dtype=int)
    won = sim.home_wins.astype(np.int16)
    wins = np.zeros((won.shape[0], n_teams), dtype=np.int16)
    np.add.at(wins.T, home, won.T)  # one row per game, added to its team's column
    np.add.at(wins.T, away, (1 - won).T)
    return wins
