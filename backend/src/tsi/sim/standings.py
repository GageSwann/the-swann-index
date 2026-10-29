"""Conference standings in every simulated season, with simplified tiebreakers (#96).

Order: conference win percentage, then head-to-head among the teams tied on it (their
win percentage in games against each other; 0.5 if they didn't meet), then the
better rating (strength in that simulation). Real tiebreakers differ by conference;
the owner accepted this simplification.

Teams are local indexes 0..k-1 within one conference; arrays carry a leading sims axis.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ConferenceGame:
    """A conference game counting toward the standings (local team indexes)."""

    home: int
    away: int
    home_won: bool | None = None  # finished games
    column: int | None = None  # remaining games: index into the simulated margins


def head_to_head(games: Sequence[ConferenceGame], home_wins: np.ndarray, k: int) -> np.ndarray:
    """(sims, k, k): wins of team i over team j in each simulation."""
    sims = home_wins.shape[0]
    wins = np.zeros((sims, k, k), dtype=np.int8)
    for g in games:
        won = home_wins[:, g.column] if g.column is not None else np.full(sims, bool(g.home_won))
        wins[:, g.home, g.away] += won
        wins[:, g.away, g.home] += ~won
    return wins


def rank(wins: np.ndarray, strength: np.ndarray, members: np.ndarray) -> np.ndarray:
    """(sims, len(members)): `members` ordered best first in each simulation."""
    w = wins[:, members][:, :, members]
    played = w + w.transpose(0, 2, 1)
    pct = w.sum(2) / np.maximum(played.sum(2), 1)
    tied = pct[:, :, None] == pct[:, None, :]  # equal fractions give equal floats
    h2h_won = (w * tied).sum(2)
    h2h_played = (played * tied).sum(2)
    h2h = np.where(h2h_played > 0, h2h_won / np.maximum(h2h_played, 1), 0.5)
    order = np.lexsort((-strength[:, members], -h2h, -pct), axis=-1)
    return members[order]
