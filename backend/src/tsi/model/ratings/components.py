"""Opponent-adjusted component ratings, one ridge fit per metric (doc 04 §2).

Each metric is fit as  y = mu + O[team] - D[opp] + hfa * site  on standardized
targets (so one penalty `lam` fits all), then put on a points-like scale:
    PPD          x average drives per game   -> points
    success rate x average plays per game    -> successful plays
    pace         drives per game (unweighted) -> drives
    tempo        plays per game (unweighted)  -> plays
Each component is centered so the average FBS team is 0; `level` keeps the
absolute value for an average FBS offense vs. an average FBS defense (e.g. points
per team-game for PPD), which the totals model needs (doc 04 §6).
For pace/tempo, A's expected drives (plays) vs. B = level + A.off - B.defense.
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
    @property
    def second_level_yards(self) -> float | None: ...
    @property
    def power_success(self) -> float | None: ...


@dataclass(frozen=True)
class MetricRatings:
    teams: dict[int, TeamRating]  # on the metric's points-like scale, FBS-centered
    hfa: float  # home-field effect on the margin, same scale
    level: float  # average FBS offense vs. average FBS defense, neutral site, same scale


@dataclass(frozen=True)
class Components:
    ppd: MetricRatings
    success: MetricRatings | None  # None when no game so far has advanced stats
    pace: MetricRatings  # drives per team-game
    tempo: MetricRatings | None  # plays per team-game (None when no play counts yet)
    games: dict[int, int]  # rated team id -> games counted (FBS, and FCS from 2022)
    # Model v1.5 (#122): rushing yards 5-10 past the line (per rush, x rushes per game) and
    # short-yardage conversion rate (x short-yardage plays per game). None without data.
    second: MetricRatings | None = None
    power: MetricRatings | None = None


def fit_components(rows: Sequence[StatRow], lam: float) -> Components | None:
    usable = [r for r in rows if involves_rated_team(r) and r.drives]
    if not usable:
        return None
    matchups = Matchups.of(usable)
    drives = np.array([r.drives for r in usable], dtype=float)
    points = np.array([r.points for r in usable], dtype=float)
    ppd = _fit_metric(matchups, points / drives, drives, lam, float(drives.mean()))
    pace = _fit_metric(matchups, drives, np.ones_like(drives), lam, 1.0)

    plays = np.array([r.plays or 0 for r in usable], dtype=float)
    has_plays = plays > 0
    tempo = None
    if has_plays.any():
        tempo = _fit_metric(
            matchups.subset(has_plays), plays[has_plays], np.ones(has_plays.sum()), lam, 1.0
        )

    # "Advanced" rows (EPA present) set the plays-per-game scale, as in the v1.1 fit.
    advanced = np.array([r.epa_per_play is not None for r in usable]) & has_plays
    success = None
    if advanced.any():
        rate = np.array([np.nan if r.success_rate is None else r.success_rate for r in usable])
        with_sr = advanced & ~np.isnan(rate)
        if with_sr.any():
            plays_pg = float(plays[advanced].mean())
            success = _fit_metric(
                matchups.subset(with_sr), rate[with_sr], plays[with_sr], lam, plays_pg
            )
    second = _fit_rate(usable, matchups, plays, "second_level_yards", SECOND_PER_GAME, lam)
    power = _fit_rate(usable, matchups, plays, "power_success", POWER_PER_GAME, lam)
    return Components(ppd, success, pace, tempo, _games_played(matchups), second, power)


SECOND_PER_GAME = 38.0  # rushes per team-game: second-level yards per rush -> per game
POWER_PER_GAME = 8.0  # short-yardage plays per team-game
MIN_ROWS = 50  # fewer team-games with the stat: no rating (early season, old data)


def _fit_rate(
    usable: Sequence[StatRow],
    matchups: Matchups,
    plays: NDArray[np.float64],
    field: str,
    per_game: float,
    lam: float,
) -> MetricRatings | None:
    """A per-play stat, weighted by plays, opponent-adjusted like success rate."""
    values = np.array([np.nan if (v := getattr(r, field)) is None else v for r in usable])
    keep = ~np.isnan(values) & (plays > 0)
    if keep.sum() < MIN_ROWS:
        return None
    return _fit_metric(matchups.subset(keep), values[keep], plays[keep], lam, per_game)


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
    off, defense = coef[2 : 2 + n], coef[2 + n : 2 + 2 * n]
    if design.has_levels:  # an FCS team = FCS level + its own (shrunk) deviation
        off = off + design.fcs * coef[-2]
        defense = defense + design.fcs * coef[-1]
    teams = {
        team: TeamRating(float(off[i]), float(defense[i])) for team, i in design.team_index.items()
    }
    centered, shift = _center_on_fbs(teams, matchups.fcs)
    return MetricRatings(centered, 2 * float(coef[1]), float(coef[0]) + shift)  # hfa: home +h


def _center_on_fbs(
    teams: dict[int, TeamRating], fcs: frozenset[int]
) -> tuple[dict[int, TeamRating], float]:
    """Shift so the average FBS team is exactly 0 (margins are unchanged by a common shift).

    Also returns mean(off) - mean(def) of the FBS teams, which moves into the level.
    """
    fbs = [t for team, t in teams.items() if not is_pooled(team) and team not in fcs]
    if not fbs:
        return teams, 0.0
    off_mean = sum(t.off for t in fbs) / len(fbs)
    def_mean = sum(t.defense for t in fbs) / len(fbs)
    centered = {
        team: TeamRating(t.off - off_mean, t.defense - def_mean) for team, t in teams.items()
    }
    return centered, off_mean - def_mean


def _games_played(matchups: Matchups) -> dict[int, int]:
    teams, counts = np.unique(matchups.team[matchups.team >= 0], return_counts=True)
    return {int(t): int(c) for t, c in zip(teams, counts, strict=True)}
