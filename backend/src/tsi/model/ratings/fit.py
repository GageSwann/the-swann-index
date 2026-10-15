"""Fit season ratings: ridge on points-per-drive and on EPA/play, blended into points.

Each metric is fit separately (doc 04 §2), standardized so one ridge penalty `lam`
works for both, then converted to points per game:
    PPD strength x average drives per game,  EPA strength x average plays per game.
    off = w * off_ppd + (1 - w) * off_epa      (same for def and home field)
Ratings are points per game vs. an average FBS team; def > 0 means a good defense.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
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


class StatRow(RatingRow, Protocol):
    @property
    def points(self) -> int: ...
    @property
    def drives(self) -> int | None: ...
    @property
    def plays(self) -> int | None: ...
    @property
    def epa_per_play(self) -> float | None: ...


@dataclass(frozen=True)
class RatingParams:
    # Preliminary defaults chosen on 2015-2022 train MAE; full tuning is a later item.
    lam: float = 2.0  # ridge penalty on standardized targets (shrinkage toward average)
    ppd_weight: float = 0.75  # w: share of the PPD fit in the blend (rest is EPA)


@dataclass(frozen=True)
class TeamRating:
    off: float  # points scored above an average FBS team
    defense: float  # points allowed below average (positive = good)

    @property
    def rating(self) -> float:
        return self.off + self.defense


@dataclass(frozen=True)
class RatingSet:
    teams: dict[int, TeamRating]  # FBS team id (or POOLED_ID) -> rating
    hfa: float  # home-field advantage in points of margin
    games: dict[int, int]  # FBS team id -> games counted

    def get(self, team_id: int, division: str) -> TeamRating:
        """Unseen teams are rated as average; non-FBS teams share the pooled rating."""
        return self.teams.get(rated_id(team_id, division), TeamRating(0.0, 0.0))


AVERAGE = RatingSet(teams={}, hfa=0.0, games={})


def fit_ratings(rows: Sequence[StatRow], params: RatingParams | None = None) -> RatingSet:
    """Ratings from completed team-game rows (this season only, before the cutoff)."""
    params = params or RatingParams()
    usable = [r for r in rows if involves_rated_team(r) and r.drives]
    if not usable:
        return AVERAGE
    drives_pg = float(np.mean([r.drives for r in usable]))
    ppd = _fit_metric(usable, lambda r: r.points / r.drives, lambda r: r.drives, params.lam)
    with_epa = [r for r in usable if r.epa_per_play is not None and r.plays]
    if with_epa:
        plays_pg = float(np.mean([r.plays for r in with_epa]))
        epa = _fit_metric(with_epa, lambda r: r.epa_per_play, lambda r: r.plays, params.lam)
        w = params.ppd_weight
    else:  # no advanced stats at all: points-per-drive only
        plays_pg, epa, w = 0.0, ppd, 1.0

    teams = {
        team: TeamRating(
            off=w * ppd.off.get(team, 0.0) * drives_pg
            + (1 - w) * epa.off.get(team, 0.0) * plays_pg,
            defense=w * ppd.defense.get(team, 0.0) * drives_pg
            + (1 - w) * epa.defense.get(team, 0.0) * plays_pg,
        )
        for team in ppd.off
    }
    hfa = 2 * (w * ppd.hfa * drives_pg + (1 - w) * epa.hfa * plays_pg)  # home +h, away -h
    return RatingSet(_center_on_fbs(teams), hfa, _games_played(usable))


def _center_on_fbs(teams: dict[int, TeamRating]) -> dict[int, TeamRating]:
    """Shift so the average FBS team is exactly 0 (margins are unchanged by a common shift)."""
    fbs = [t for team, t in teams.items() if team != POOLED_ID]
    if not fbs:
        return teams
    off_mean = sum(t.off for t in fbs) / len(fbs)
    def_mean = sum(t.defense for t in fbs) / len(fbs)
    return {team: TeamRating(t.off - off_mean, t.defense - def_mean) for team, t in teams.items()}


@dataclass(frozen=True)
class _MetricFit:
    off: dict[int, float]
    defense: dict[int, float]
    hfa: float


def _fit_metric(
    rows: Sequence[StatRow],
    target: Callable[[StatRow], float],
    weight: Callable[[StatRow], float],
    lam: float,
) -> _MetricFit:
    design = build_design(rows)
    y = np.array([target(r) for r in rows], dtype=float)
    w = np.array([weight(r) for r in rows], dtype=float)
    w /= w.mean()
    scale = float(y.std()) or 1.0
    coef = weighted_ridge(design.x, y / scale, w, lam, design.penalized) * scale
    n = design.n_teams
    off = {team: float(coef[2 + i]) for team, i in design.team_index.items()}
    defense = {team: float(coef[2 + n + i]) for team, i in design.team_index.items()}
    return _MetricFit(off, defense, float(coef[1]))


def _games_played(rows: Sequence[StatRow]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for r in rows:
        team = rated_id(r.team_id, r.team_div)
        if team != POOLED_ID:
            counts[team] = counts.get(team, 0) + 1
    return counts


def predicted_margin(
    ratings: RatingSet, home: TeamRating, away: TeamRating, neutral: bool
) -> float:
    """Home-view margin: (home off - away def) - (away off - home def) + HFA."""
    margin = (home.off - away.defense) - (away.off - home.defense)
    return margin + (0.0 if neutral else ratings.hfa)
