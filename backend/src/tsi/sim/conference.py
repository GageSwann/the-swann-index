"""Conference title games in every simulated season.

Finalists: the top two in the standings, or each division's winner when the conference
plays in divisions (sim/standings.py). The title game is at a neutral site: its mean
margin comes from the published model (the caller passes a matrix of neutral-site
margins), plus both teams' rating shifts and game noise from the same simulation.
Once the real title game is on the schedule, its finalists are fixed and its winner
comes from that game instead.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from tsi.sim.season import SimulatedGames
from tsi.sim.standings import ConferenceGame, head_to_head, rank


@dataclass(frozen=True)
class Conference:
    name: str
    teams: tuple[int, ...]  # simulation team indexes; local index = position here
    games: tuple[ConferenceGame, ...]  # standings games (local indexes)
    neutral_margin: np.ndarray  # (k, k): mean margin of i vs j at a neutral site
    divisions: tuple[tuple[int, ...], ...] | None = None  # local indexes per division
    title_game: ConferenceGame | None = None  # once scheduled (local indexes)


@dataclass(frozen=True)
class TitleResults:
    finalists: np.ndarray  # (sims, 2) simulation team indexes
    champion: np.ndarray  # (sims,) simulation team index
    added_game: bool  # True when the title game was simulated here (not on the schedule)


def simulate_title(conf: Conference, sim: SimulatedGames) -> TitleResults:
    teams = np.array(conf.teams)
    k = len(teams)
    shift = sim.shift[:, teams]
    if conf.title_game is not None:
        g = conf.title_game
        home_won = sim.home_wins[:, g.column] if g.column is not None else bool(g.home_won)
        pair = np.broadcast_to(np.array([g.home, g.away]), (shift.shape[0], 2))
        champion = np.where(home_won, g.home, g.away)
        return TitleResults(teams[pair], teams[champion], added_game=False)

    wins = head_to_head(conf.games, sim.home_wins, k)
    others = (conf.neutral_margin.sum(1) / max(k - 1, 1))[None, :]  # avg margin vs the rest
    strength = others + shift
    if conf.divisions:
        a, b = (rank(wins, strength, np.array(d))[:, 0] for d in conf.divisions)
    else:
        top = rank(wins, strength, np.arange(k))
        a, b = top[:, 0], top[:, 1]
    rows = np.arange(shift.shape[0])
    margin = (
        conf.neutral_margin[a, b]
        + shift[rows, a]
        - shift[rows, b]
        + sim.rng.normal(0.0, sim.noise, len(rows))
    )
    champion = np.where(margin > 0, a, b)
    return TitleResults(teams[np.stack([a, b], axis=1)], teams[champion], added_game=True)


def title_odds(results: TitleResults, team_index: Sequence[int]) -> dict[int, tuple[float, float]]:
    """team index -> (P(plays in the title game), P(wins the conference))."""
    sims = len(results.champion)
    out = {}
    for t in team_index:
        finalist = (results.finalists == t).any(axis=1).sum() / sims
        out[t] = (float(finalist), float((results.champion == t).sum() / sims))
    return out
