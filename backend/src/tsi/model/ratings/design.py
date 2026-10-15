"""Turn team-game rows into a regression design: y = mu + O[team] - D[opp] + hfa * site.

Column layout: [intercept, hfa, O_0..O_{n-1}, D_0..D_{n-1}].
Non-FBS teams are pooled into one pseudo-team (`POOLED_ID`) so FBS-vs-FCS games
inform FBS ratings without needing full FCS ratings (doc 04 §5). Games between
two non-FBS teams carry no FBS information and are dropped.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

POOLED_ID = -1  # stands in for every non-FBS team
RATED_DIVISION = "fbs"


class RatingRow(Protocol):
    """One team's offense in one game (e.g. `db.queries.stats.OffenseRow`)."""

    @property
    def team_id(self) -> int: ...
    @property
    def opp_id(self) -> int: ...
    @property
    def team_div(self) -> str: ...
    @property
    def opp_div(self) -> str: ...
    @property
    def site(self) -> int: ...


def rated_id(team_id: int, division: str) -> int:
    return team_id if division == RATED_DIVISION else POOLED_ID


def involves_rated_team(row: RatingRow) -> bool:
    return RATED_DIVISION in (row.team_div, row.opp_div)


@dataclass(frozen=True)
class Design:
    x: NDArray[np.float64]
    penalized: NDArray[np.bool_]
    team_index: dict[int, int]  # rated id -> position in O/D blocks

    @property
    def n_teams(self) -> int:
        return len(self.team_index)


def build_design(rows: Sequence[RatingRow]) -> Design:
    """Design matrix for rows that already passed `involves_rated_team`."""
    ids = sorted(
        {rated_id(r.team_id, r.team_div) for r in rows}
        | {rated_id(r.opp_id, r.opp_div) for r in rows}
    )
    team_index = {team: i for i, team in enumerate(ids)}
    n = len(ids)
    x = np.zeros((len(rows), 2 + 2 * n))
    x[:, 0] = 1.0
    for i, row in enumerate(rows):
        x[i, 1] = row.site
        x[i, 2 + team_index[rated_id(row.team_id, row.team_div)]] = 1.0
        x[i, 2 + n + team_index[rated_id(row.opp_id, row.opp_div)]] = -1.0
    penalized = np.ones(2 + 2 * n, dtype=bool)
    penalized[:2] = False  # intercept and home-field are not shrunk
    return Design(x, penalized, team_index)
