"""Run Elo over every completed game and score it against the closing line.

Elo itself is walk-forward (each prediction uses only earlier games). The one
fitted number, points per Elo, is fit on the TRAIN seasons only and then applied
everywhere, so the validation seasons stay out-of-sample.
Scored set: completed FBS-vs-FBS games with a closing spread, 2015 onward.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from sqlalchemy.orm import Session

from tsi.backtest.evaluate import ScoredGame, Summary, summarize_by_season, summarize_period
from tsi.db.queries.market import closing_spreads
from tsi.db.queries.results import GameResult, completed_games
from tsi.model.elo import EloParams, fit_points_per_elo, run_elo

TRAIN = (2015, 2022)
VALIDATE = (2023, 2025)
FIRST_SCORED_SEASON = 2015  # 2014 only warms ratings up


@dataclass(frozen=True)
class EloPick:
    margin: float  # points, home view
    home_win_prob: float


@dataclass(frozen=True)
class EloReport:
    params: EloParams
    seasons: list[Summary]
    periods: list[Summary]


def is_scored(game: GameResult, closing: Mapping[int, float]) -> bool:
    return game.fbs_vs_fbs and game.season >= FIRST_SCORED_SEASON and game.id in closing


def elo_picks(
    games: Sequence[GameResult], closing: Mapping[int, float], params: EloParams
) -> tuple[EloParams, dict[int, EloPick]]:
    """Walk-forward Elo for every game; points-per-Elo fit on scored TRAIN games only."""
    preds = run_elo(games, params).predictions
    train = [
        (g, p)
        for g, p in zip(games, preds, strict=True)
        if is_scored(g, closing) and TRAIN[0] <= g.season <= TRAIN[1]
    ]
    scale = fit_points_per_elo([p.elo_diff for _, p in train], [g.margin for g, _ in train])
    fitted = replace(params, elo_per_point=scale)
    picks = {p.game_id: EloPick(p.elo_diff / scale, p.home_win_prob) for p in preds}
    return fitted, picks


def period_summaries(scored: Sequence[ScoredGame], through_season: int) -> list[Summary]:
    periods = [
        summarize_period(f"Train {TRAIN[0]}-{TRAIN[1]}", scored, *TRAIN),
        summarize_period(f"Validate {VALIDATE[0]}-{VALIDATE[1]}", scored, *VALIDATE),
    ]
    if through_season > VALIDATE[1]:
        periods.append(
            summarize_period(f"{through_season} to date", scored, through_season, through_season)
        )
    return periods


def run_elo_report(
    session: Session, through_season: int, params: EloParams | None = None
) -> EloReport:
    games = completed_games(session, through_season)
    closing = closing_spreads(session, through_season)
    fitted, picks = elo_picks(games, closing, params or EloParams())
    scored = [
        ScoredGame(
            season=g.season,
            pred_margin=picks[g.id].margin,
            home_win_prob=picks[g.id].home_win_prob,
            actual_margin=g.margin,
            market_margin=-closing[g.id],
        )
        for g in games
        if is_scored(g, closing)
    ]
    return EloReport(fitted, summarize_by_season(scored), period_summaries(scored, through_season))
