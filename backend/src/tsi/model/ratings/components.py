"""Opponent-adjusted component ratings, one ridge fit per metric (doc 04 §2).

Each metric is fit as  y = mu + O[team] - D[opp] + hfa * site  on standardized
targets (so one penalty `lam` fits all), then put on a points-like scale:
    PPD          x average drives per game   -> points
    success rate x average plays per game    -> successful plays
Each component is centered so the average FBS team is 0.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from tsi.model.ratings.design import (
    Matchups,
    RatingRow,
    build_design,
    involves_rated_team,
    is_pooled,
)
from tsi.model.ratings.ridge import solve_normal
from tsi.model.ratings.types import TeamRating


class StatRow(RatingRow, Protocol):
    @property
    def points(self) -> int: ...
    @property
    def drives(self) -> int | None: ...
    @property
    def plays(self) -> int | None: ...
    @property
    def epa_per_play(self) -> float | None: ...
    @property
    def success_rate(self) -> float | None: ...
    @property
    def start_time(self) -> datetime | None: ...


@dataclass(frozen=True)
class MetricRatings:
    teams: dict[int, TeamRating]  # on the metric's points-like scale, FBS-centered
    hfa: float  # home-field effect on the margin, same scale


@dataclass(frozen=True)
class Components:
    ppd: MetricRatings
    success: MetricRatings | None  # None when no game so far has advanced stats
    games: dict[int, int]  # FBS team id -> games counted


def fit_components(rows: Sequence[StatRow], lam: float) -> Components | None:
    usable = [r for r in rows if involves_rated_team(r) and r.drives]
    if not usable:
        return None
    matchups = Matchups.of(usable)
    drives = np.array([r.drives for r in usable], dtype=float)
    points = np.array([r.points for r in usable], dtype=float)
    ppd = _fit_metric(matchups, points / drives, drives, lam, float(drives.mean()))

    # "Advanced" rows (EPA present) set the plays-per-game scale, as in the v1.1 fit.
    advanced = np.array([r.epa_per_play is not None and bool(r.plays) for r in usable])
    success = None
    if advanced.any():
        plays = np.array([r.plays or 0 for r in usable], dtype=float)
        rate = np.array([np.nan if r.success_rate is None else r.success_rate for r in usable])
        with_sr = advanced & ~np.isnan(rate)
        if with_sr.any():
            plays_pg = float(plays[advanced].mean())
            success = _fit_metric(
                matchups.subset(with_sr), rate[with_sr], plays[with_sr], lam, plays_pg
            )
    return Components(ppd, success, _games_played(matchups))


def _fit_metric(
    matchups: Matchups,
    y: NDArray[np.float64],
    w: NDArray[np.float64],
    lam: float,
    per_game: float,
) -> MetricRatings:
    design = build_design(matchups)
    scale = float(y.std()) or 1.0
    gram, rhs = design.normal_equations(y / scale, w / w.mean())
    coef = solve_normal(gram, rhs, lam, design.penalized) * scale * per_game
    n = design.n_teams
    teams = {
        team: TeamRating(float(coef[2 + i]), float(coef[2 + n + i]))
        for team, i in design.team_index.items()
    }
    return MetricRatings(_center_on_fbs(teams), 2 * float(coef[1]))  # home +h, away -h


def _center_on_fbs(teams: dict[int, TeamRating]) -> dict[int, TeamRating]:
    """Shift so the average FBS team is exactly 0 (margins are unchanged by a common shift)."""
    fbs = [t for team, t in teams.items() if not is_pooled(team)]
    if not fbs:
        return teams
    off_mean = sum(t.off for t in fbs) / len(fbs)
    def_mean = sum(t.defense for t in fbs) / len(fbs)
    return {team: TeamRating(t.off - off_mean, t.defense - def_mean) for team, t in teams.items()}


def _games_played(matchups: Matchups) -> dict[int, int]:
    teams, counts = np.unique(matchups.team[matchups.team >= 0], return_counts=True)
    return {int(t): int(c) for t, c in zip(teams, counts, strict=True)}
