"""Turn team-game rows into a regression design: y = mu + O[team] - D[opp] + hfa * site.

Column layout: [intercept, hfa, O_0..O_{n-1}, D_0..D_{n-1}], plus two unpenalized FCS
level columns [L_off, L_def] when the fit rates FCS teams individually (decision #109):
    y = ... + L_off * [team is FCS] - L_def * [opp is FCS]
so FCS teams shrink toward the FCS mean rather than the FBS mean.
Teams not rated individually are pooled into pseudo-teams (FCS before FCS_STATS_FROM,
and everything below FCS) so their games still inform the rated teams (doc 04 §5).
Games between two pooled teams carry no information and are dropped.

Each row has only three nonzero columns, so the design is kept sparse (index
arrays) and the normal equations X'WX, X'Wy are assembled directly with
`bincount`, which is far cheaper than multiplying a dense matrix.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from tsi.divisions import FCS, is_individual_fcs, rated_individually

FCS_POOL_ID = -1  # stands in for every FCS team (seasons before FCS_STATS_FROM)
LOWER_POOL_ID = -2  # D-II, D-III, NAIA and unclassified teams


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
    @property
    def season(self) -> int: ...


def rated_id(team_id: int, division: str, season: int) -> int:
    if rated_individually(division, season):
        return team_id
    return FCS_POOL_ID if division == FCS else LOWER_POOL_ID


def is_pooled(team: int) -> bool:
    return team < 0


def involves_rated_team(row: RatingRow) -> bool:
    return rated_individually(row.team_div, row.season) or rated_individually(
        row.opp_div, row.season
    )


@dataclass(frozen=True)
class Matchups:
    """Rated ids and site per row, computed once and shared by every metric fit."""

    team: NDArray[np.int64]
    opp: NDArray[np.int64]
    site: NDArray[np.float64]
    fcs: frozenset[int] = frozenset()  # individually rated FCS team ids (get the FCS level)

    @classmethod
    def of(cls, rows: Sequence[RatingRow]) -> "Matchups":
        fcs = {r.team_id for r in rows if is_individual_fcs(r.team_div, r.season)}
        fcs |= {r.opp_id for r in rows if is_individual_fcs(r.opp_div, r.season)}
        return cls(
            np.array([rated_id(r.team_id, r.team_div, r.season) for r in rows], dtype=np.int64),
            np.array([rated_id(r.opp_id, r.opp_div, r.season) for r in rows], dtype=np.int64),
            np.array([r.site for r in rows], dtype=float),
            frozenset(fcs),
        )

    def subset(self, mask: NDArray[np.bool_]) -> "Matchups":
        return Matchups(self.team[mask], self.opp[mask], self.site[mask], self.fcs)


@dataclass(frozen=True)
class Design:
    off: NDArray[np.intp]  # row -> position of its offense in the O block
    opp: NDArray[np.intp]  # row -> position of its opponent in the D block
    site: NDArray[np.float64]
    team_index: dict[int, int]  # rated id -> position in O/D blocks
    fcs: NDArray[np.bool_]  # position -> individually rated FCS team (gets the FCS level)

    @property
    def n_teams(self) -> int:
        return len(self.team_index)

    @property
    def has_levels(self) -> bool:
        return bool(self.fcs.any())

    @property
    def n_columns(self) -> int:
        return 2 + 2 * self.n_teams + (2 if self.has_levels else 0)

    @property
    def penalized(self) -> NDArray[np.bool_]:
        penalized = np.ones(self.n_columns, dtype=bool)
        penalized[:2] = False  # intercept and home-field are not shrunk
        if self.has_levels:
            penalized[-2:] = False  # nor the FCS levels
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
        gram[0, 0], gram[1, 1] = w.sum(), (ws * s).sum()
        gram[0, 1] = gram[1, 0] = ws.sum()
        gram[0, o] = gram[o, 0] = w_off
        gram[0, d] = gram[d, 0] = -w_opp
        gram[1, o] = gram[o, 1] = s_off
        gram[1, d] = gram[d, 1] = -s_opp
        cross = -np.bincount(off * n + opp, w, n * n).reshape(n, n)
        gram[o, d], gram[d, o] = cross, cross.T  # symmetric: fill both blocks directly
        idx = np.arange(n)
        gram[2 + idx, 2 + idx] = w_off
        gram[2 + n + idx, 2 + n + idx] = w_opp

        rhs = np.concatenate(
            ([wy.sum(), (wy * s).sum()], np.bincount(off, wy, n), -np.bincount(opp, wy, n))
        )
        if not self.has_levels:
            return gram, rhs
        return self._with_levels(gram, rhs, y, w)

    def _with_levels(
        self,
        gram: NDArray[np.float64],
        rhs: NDArray[np.float64],
        y: NDArray[np.float64],
        w: NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Append the FCS level columns: a = [offense is FCS], b = -[opponent is FCS]."""
        n, s, off, opp = self.n_teams, self.site, self.off, self.opp
        a, b = self.fcs[off].astype(float), self.fcs[opp].astype(float)
        wa, wb = w * a, w * b
        o, d = slice(2, 2 + n), slice(2 + n, 2 + 2 * n)
        lo, ld = 2 + 2 * n, 3 + 2 * n
        full = np.zeros((self.n_columns, self.n_columns))
        full[:lo, :lo] = gram
        full[lo, lo], full[ld, ld] = wa.sum(), wb.sum()
        full[lo, ld] = full[ld, lo] = -(wa * b).sum()
        full[0, lo] = full[lo, 0] = wa.sum()
        full[0, ld] = full[ld, 0] = -wb.sum()
        full[1, lo] = full[lo, 1] = (wa * s).sum()
        full[1, ld] = full[ld, 1] = -(wb * s).sum()
        full[o, lo] = full[lo, o] = np.bincount(off, wa, n)
        full[d, lo] = full[lo, d] = -np.bincount(opp, wa, n)
        full[o, ld] = full[ld, o] = -np.bincount(off, wb, n)
        full[d, ld] = full[ld, d] = np.bincount(opp, wb, n)
        return full, np.concatenate((rhs, [(wa * y).sum(), -(wb * y).sum()]))


def build_design(matchups: Matchups) -> Design:
    """Design for rows that already passed `involves_rated_team`."""
    ids, inverse = np.unique(np.concatenate((matchups.team, matchups.opp)), return_inverse=True)
    rows = len(matchups.team)
    team_index = {int(team): i for i, team in enumerate(ids)}
    fcs = np.array([int(team) in matchups.fcs for team in ids], dtype=bool)
    return Design(inverse[:rows], inverse[rows:], matchups.site, team_index, fcs)
