"""Margin-aware Elo: the baseline the main model must clearly beat (doc 04 §8).

Games are processed in kickoff order. Each prediction is made from ratings
*before* the game, and ratings update only after it, so there is no look-ahead.
Between seasons, ratings regress part of the way back to their division's mean.

Formulas (FiveThirtyEight-style):
    diff     = home - away + HFA (0 at neutral sites)
    P(home)  = 1 / (1 + 10^(-diff / 400))
    mult     = ln(|margin| + 1) * 2.2 / (0.001 * winner_diff + 2.2)
    delta    = K * mult * (result - P(home))
"""

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Protocol

DEFAULT_DIVISION_MEANS: Mapping[str, float] = {
    "fbs": 1500.0,
    "fcs": 1300.0,
    "ii": 1100.0,
    "iii": 1000.0,
}
UNKNOWN_DIVISION_MEAN = 1000.0


@dataclass(frozen=True)
class EloParams:
    # Defaults tuned on 2015-2022 FBS-vs-FBS games by margin MAE (validation untouched).
    k: float = 45.0
    hfa: float = 55.0  # Elo points for home field
    carryover: float = 0.90  # share of distance from the mean kept between seasons
    elo_per_point: float = 22.0  # Elo diff per point of spread; refit on train seasons
    division_means: Mapping[str, float] = field(default_factory=lambda: DEFAULT_DIVISION_MEANS)

    def mean_for(self, division: str) -> float:
        return self.division_means.get(division, UNKNOWN_DIVISION_MEAN)


class EloGame(Protocol):
    """Any completed game record with these fields (e.g. `db.queries.results.GameResult`)."""

    @property
    def id(self) -> int: ...
    @property
    def season(self) -> int: ...
    @property
    def home_id(self) -> int: ...
    @property
    def away_id(self) -> int: ...
    @property
    def home_div(self) -> str: ...
    @property
    def away_div(self) -> str: ...
    @property
    def neutral(self) -> bool: ...
    @property
    def home_points(self) -> int: ...
    @property
    def away_points(self) -> int: ...


@dataclass(frozen=True)
class EloPrediction:
    """Made from pre-game ratings only."""

    game_id: int
    elo_diff: float  # home - away + HFA
    home_win_prob: float
    pred_margin: float  # home view, positive = home favored


@dataclass
class EloRun:
    predictions: list[EloPrediction]
    ratings: dict[int, float]  # after the last game processed


def home_win_prob(elo_diff: float) -> float:
    return 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))


def margin_multiplier(margin: int, winner_elo_diff: float) -> float:
    """Bigger wins move ratings more; expected blowouts by favorites move them less."""
    return math.log(abs(margin) + 1) * 2.2 / (0.001 * winner_elo_diff + 2.2)


def run_elo(games: Iterable[EloGame], params: EloParams | None = None) -> EloRun:
    """Process games in the given (kickoff) order; return pre-game predictions."""
    params = params or EloParams()
    ratings: dict[int, float] = {}
    last_division: dict[int, str] = {}
    predictions: list[EloPrediction] = []
    season: int | None = None

    for game in games:
        if season is not None and game.season != season:
            _regress_to_mean(ratings, last_division, params)
        season = game.season
        last_division[game.home_id] = game.home_div
        last_division[game.away_id] = game.away_div
        home = ratings.setdefault(game.home_id, params.mean_for(game.home_div))
        away = ratings.setdefault(game.away_id, params.mean_for(game.away_div))

        diff = home - away + (0.0 if game.neutral else params.hfa)
        p_home = home_win_prob(diff)
        predictions.append(EloPrediction(game.id, diff, p_home, diff / params.elo_per_point))

        margin = game.home_points - game.away_points
        result = 1.0 if margin > 0 else 0.0 if margin < 0 else 0.5
        winner_diff = diff if margin >= 0 else -diff
        delta = params.k * margin_multiplier(margin, winner_diff) * (result - p_home)
        ratings[game.home_id] = home + delta
        ratings[game.away_id] = away - delta

    return EloRun(predictions, ratings)


def _regress_to_mean(
    ratings: dict[int, float], last_division: Mapping[int, str], params: EloParams
) -> None:
    for team_id, rating in ratings.items():
        mean = params.mean_for(last_division[team_id])
        ratings[team_id] = mean + params.carryover * (rating - mean)


def fit_points_per_elo(elo_diffs: Iterable[float], margins: Iterable[float]) -> float:
    """Least-squares slope (through the origin) of margin on Elo diff, as Elo per point."""
    pairs = list(zip(elo_diffs, margins, strict=True))
    xy = sum(d * m for d, m in pairs)
    xx = sum(d * d for d, _ in pairs)
    if xy <= 0:
        raise ValueError("Elo differences don't predict margins; check the inputs")
    return xx / xy
