"""Summarize scored games by season or period, side by side with the closing line."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from tsi.backtest.metrics import brier, log_loss, mae, rmse, straight_up_accuracy


@dataclass(frozen=True)
class ScoredGame:
    season: int
    pred_margin: float  # model, home view, positive = home favored
    home_win_prob: float
    actual_margin: int
    market_margin: float  # closing line as a margin: -spread


@dataclass(frozen=True)
class Summary:
    label: str
    games: int
    mae: float
    rmse: float
    su_accuracy: float
    brier: float
    log_loss: float
    market_mae: float
    market_su_accuracy: float


def summarize(label: str, games: Sequence[ScoredGame]) -> Summary:
    pred = [g.pred_margin for g in games]
    actual = [g.actual_margin for g in games]
    market = [g.market_margin for g in games]
    probs = [g.home_win_prob for g in games]
    outcomes = [1.0 if a > 0 else 0.0 if a < 0 else 0.5 for a in actual]
    return Summary(
        label=label,
        games=len(games),
        mae=mae(pred, actual),
        rmse=rmse(pred, actual),
        su_accuracy=straight_up_accuracy(pred, actual),
        brier=brier(probs, outcomes),
        log_loss=log_loss(probs, outcomes),
        market_mae=mae(market, actual),
        market_su_accuracy=straight_up_accuracy(market, actual),
    )


def summarize_by_season(games: Iterable[ScoredGame]) -> list[Summary]:
    by_season: dict[int, list[ScoredGame]] = {}
    for game in games:
        by_season.setdefault(game.season, []).append(game)
    return [summarize(str(s), by_season[s]) for s in sorted(by_season)]


def summarize_period(label: str, games: Iterable[ScoredGame], first: int, last: int) -> Summary:
    return summarize(label, [g for g in games if first <= g.season <= last])
