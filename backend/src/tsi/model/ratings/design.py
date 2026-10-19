"""Turn team-game rows into a regression design: y = mu + O[team] - D[opp] + hfa * site.

Column layout: [intercept, hfa, O_0..O_{n-1}, D_0..D_{n-1}].
Non-FBS teams are pooled into pseudo-teams (FCS, and everything below FCS) so FBS-vs-FCS games
inform FBS ratings without needing full FCS ratings (doc 04 §5). Games between
two non-FBS teams carry no FBS information and are dropped.

Each row has only three nonzero columns, so the design is kept sparse (index
arrays) and the normal equations X'WX, X'Wy are assembled directly with
`bincount`, which is far cheaper than multiplying a dense matrix.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

FCS_POOL_ID = -1  # stands in for every FCS team
LOWER_POOL_ID = -2  # D-II, D-III, NAIA and unclassified teams
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
    if division == RATED_DIVISION:
        return team_id
    return FCS_POOL_ID if division == "fcs" else LOWER_POOL_ID


def is_pooled(team: int) -> bool:
    return team < 0


def involves_rated_team(row: RatingRow) -> bool:
    return RATED_DIVISION in (row.team_div, row.opp_div)


@dataclass(frozen=True)
class Matchups:
    """Rated ids and site per row, computed once and shared by every metric fit."""

    team: NDArray[np.int64]
    opp: NDArray[np.int64]
    site: NDArray[np.float64]

    @classmethod
    def of(cls, rows: Sequence[RatingRow]) -> "Matchups":
        return cls(
            np.array([rated_id(r.team_id, r.team_div) for r in rows], dtype=np.int64),
            np.array([rated_id(r.opp_id, r.opp_div) for r in rows], dtype=np.int64),
            np.array([r.site for r in rows], dtype=float),
        )

    def subset(self, mask: NDArray[np.bool_]) -> "Matchups":
        return Matchups(self.team[mask], self.opp[mask], self.site[mask])


@dataclass(frozen=True)
class Design:
    off: NDArray[np.intp]  # row -> position of its offense in the O block
    opp: NDArray[np.intp]  # row -> position of its opponent in the D block
    site: NDArray[np.float64]
    team_index: dict[int, int]  # rated id -> position in O/D blocks

    @property
    def n_teams(self) -> int:
        return len(self.team_index)

    @property
    def penalized(self) -> NDArray[np.bool_]:
        penalized = np.ones(2 + 2 * self.n_teams, dtype=bool)
        penalized[:2] = False  # intercept and home-field are not shrunk
        return penalized

    def normal_equations(
        self, y: NDArray[np.float64], w: NDArray[np.float64]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """(X'WX, X'Wy) without materializing X."""
        n, s, off, opp = self.n_teams, self.site, self.off, self.opp
        ws, wy = w * s, w * y
        w_off, w_opp = np.bincount(off, w, n), np.bincount(opp, w, n)
        s_off, s_opp = np.bincount(off, ws, n), np.bincount(opp, ws, n)
        o, d = slice(2, 2 + n), slice(2 + n, 2 + 2 * n)

        gram = np.zeros((2 + 2 * n, 2 + 2 * n))
        gram[0, 0], gram[0, 1], gram[1, 1] = w.sum(), ws.sum(), (ws * s).sum()
        gram[0, o], gram[0, d] = w_off, -w_opp
        gram[1, o], gram[1, d] = s_off, -s_opp
        gram[o, d] = -np.bincount(off * n + opp, w, n * n).reshape(n, n)
        gram[o, o] = np.diag(w_off)
        gram[d, d] = np.diag(w_opp)
        upper = np.triu_indices(2 + 2 * n, 1)
        gram.T[upper] = gram[upper]  # mirror the upper triangle

        rhs = np.concatenate(
            ([wy.sum(), (wy * s).sum()], np.bincount(off, wy, n), -np.bincount(opp, wy, n))
        )
        return gram, rhs


def build_design(matchups: Matchups) -> Design:
    """Design for rows that already passed `involves_rated_team`."""
    ids, inverse = np.unique(np.concatenate((matchups.team, matchups.opp)), return_inverse=True)
    rows = len(matchups.team)
    team_index = {int(team): i for i, team in enumerate(ids)}
    return Design(inverse[:rows], inverse[rows:], matchups.site, team_index)
