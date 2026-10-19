"""Walk-forward Elo margins for every game, with points-per-Elo fit on chosen seasons."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from tsi.backtest.splits import TRAIN, is_scored
from tsi.db.queries.results import GameResult
from tsi.model.elo import EloParams, fit_points_per_elo, run_elo


@dataclass(frozen=True)
class EloPick:
    margin: float  # points, home view
    home_win_prob: float


def elo_picks(
    games: Sequence[GameResult],
    closing: Mapping[int, float],
    params: EloParams,
    fit_seasons: tuple[int, int] = TRAIN,
) -> tuple[EloParams, dict[int, EloPick]]:
    """Walk-forward Elo for every game; points-per-Elo fit on scored `fit_seasons` games."""
    preds = run_elo(games, params).predictions
    train = [
        (g, p)
        for g, p in zip(games, preds, strict=True)
        if is_scored(g, closing) and fit_seasons[0] <= g.season <= fit_seasons[1]
    ]
    scale = fit_points_per_elo([p.elo_diff for _, p in train], [g.margin for g, _ in train])
    fitted = replace(params, elo_per_point=scale)
    picks = {p.game_id: EloPick(p.elo_diff / scale, p.home_win_prob) for p in preds}
    return fitted, picks
