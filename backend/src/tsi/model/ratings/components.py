"""Opponent-adjusted component ratings, one ridge fit per metric (doc 04 §2).

Each metric is fit as  y = mu + O[team] - D[opp] + hfa * site  on standardized
targets (so one penalty `lam` fits all), then put on a points-like scale:
    PPD          x average drives per game   -> points
    EPA/play     x average plays per game    -> expected points
    success rate x average plays per game    -> successful plays
Each component is centered so the average FBS team is 0.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

import numpy as np

from tsi.model.ratings.design import (
    POOLED_ID,
    RatingRow,
    build_design,
    involves_rated_team,
    rated_id,
)
from tsi.model.ratings.ridge import weighted_ridge
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
    epa: MetricRatings | None  # None when no game so far has advanced stats
    success: MetricRatings | None
    games: dict[int, int]  # FBS team id -> games counted


def fit_components(rows: Sequence[StatRow], lam: float) -> Components | None:
    usable = [r for r in rows if involves_rated_team(r) and r.drives]
    if not usable:
        return None
    drives_pg = float(np.mean([r.drives for r in usable]))
    ppd = _fit_metric(usable, lambda r: r.points / r.drives, lambda r: r.drives, lam, drives_pg)
    advanced = [r for r in usable if r.epa_per_play is not None and r.plays]
    epa = success = None
    if advanced:
        plays_pg = float(np.mean([r.plays for r in advanced]))
        epa = _fit_metric(advanced, lambda r: r.epa_per_play, lambda r: r.plays, lam, plays_pg)
        with_sr = [r for r in advanced if r.success_rate is not None]
        if with_sr:
            success = _fit_metric(
                with_sr, lambda r: r.success_rate, lambda r: r.plays, lam, plays_pg
            )
    return Components(ppd, epa, success, _games_played(usable))


def _fit_metric(
    rows: Sequence[StatRow],
    target: Callable[[StatRow], float],
    weight: Callable[[StatRow], float],
    lam: float,
    per_game: float,
) -> MetricRatings:
    design = build_design(rows)
    y = np.array([target(r) for r in rows], dtype=float)
    w = np.array([weight(r) for r in rows], dtype=float)
    w /= w.mean()
    scale = float(y.std()) or 1.0
    coef = weighted_ridge(design.x, y / scale, w, lam, design.penalized) * scale * per_game
    n = design.n_teams
    teams = {
        team: TeamRating(float(coef[2 + i]), float(coef[2 + n + i]))
        for team, i in design.team_index.items()
    }
    return MetricRatings(_center_on_fbs(teams), 2 * float(coef[1]))  # home +h, away -h


def _center_on_fbs(teams: dict[int, TeamRating]) -> dict[int, TeamRating]:
    """Shift so the average FBS team is exactly 0 (margins are unchanged by a common shift)."""
    fbs = [t for team, t in teams.items() if team != POOLED_ID]
    if not fbs:
        return teams
    off_mean = sum(t.off for t in fbs) / len(fbs)
    def_mean = sum(t.defense for t in fbs) / len(fbs)
    return {team: TeamRating(t.off - off_mean, t.defense - def_mean) for team, t in teams.items()}


def _games_played(rows: Sequence[StatRow]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for r in rows:
        team = rated_id(r.team_id, r.team_div)
        if team != POOLED_ID:
            counts[team] = counts.get(team, 0) + 1
    return counts
