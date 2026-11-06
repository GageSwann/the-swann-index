"""What one game is worth: how much a win instead of a loss moves a team's season.

Read from the season simulation itself, no extra simulations: across the simulated
seasons, compare how often the team made the playoff field (or won its conference) when
it won this game with how often it did when it lost. Games of the week use it as the
"stakes" of a game (Phase 13.4, decision #141).
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TeamStakes:
    playoff: float | None  # P(in the field | win) - P(in the field | loss); None: no field
    title: float | None  # the same for its conference title; None: no conference race


@dataclass(frozen=True)
class GameStakes:
    home: TeamStakes
    away: TeamStakes


def swing(won: np.ndarray, outcome: np.ndarray) -> float:
    """P(outcome | won) - P(outcome | lost) over the simulated seasons; 0 when the game
    went the same way in every simulation (nothing to compare)."""
    wins, losses = won.sum(), (~won).sum()
    if wins == 0 or losses == 0:
        return 0.0
    return float(outcome[won].mean() - outcome[~won].mean())


def team_stakes(
    team: int,  # simulation team index
    won: np.ndarray,  # (sims,) True where this team won the game
    field: np.ndarray | None,  # (sims, field_size) simulation team indexes in the field
    champion: np.ndarray | None,  # (sims,) its conference champion's simulation index
) -> TeamStakes:
    playoff = None if field is None else swing(won, (field == team).any(axis=1))
    title = None if champion is None else swing(won, champion == team)
    return TeamStakes(playoff, title)


def stakes_value(s: TeamStakes) -> float:
    """One number in 0..1: the playoff swing plus half the conference-title swing."""
    return min(1.0, max(0.0, s.playoff or 0.0) + 0.5 * max(0.0, s.title or 0.0))
