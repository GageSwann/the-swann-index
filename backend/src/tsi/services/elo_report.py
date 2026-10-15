"""Run Elo over every completed game and score it against the closing line.

Elo itself is walk-forward (each prediction uses only earlier games). The one
fitted number, points per Elo, is fit on the TRAIN seasons only and then applied
everywhere, so the validation seasons stay out-of-sample.
Scored set: completed FBS-vs-FBS games with a closing spread.
"""

from dataclasses import dataclass, replace

from sqlalchemy.orm import Session

from tsi.backtest.evaluate import ScoredGame, Summary, summarize_by_season, summarize_period
from tsi.db.queries.market import closing_spreads
from tsi.db.queries.results import completed_games
from tsi.model.elo import EloParams, fit_points_per_elo, run_elo

TRAIN = (2015, 2022)
VALIDATE = (2023, 2025)
FIRST_SCORED_SEASON = 2015  # 2014 only warms ratings up


@dataclass(frozen=True)
class EloReport:
    params: EloParams
    seasons: list[Summary]
    periods: list[Summary]


def run_elo_report(
    session: Session, through_season: int, params: EloParams | None = None
) -> EloReport:
    params = params or EloParams()
    games = completed_games(session, through_season)
    closing = closing_spreads(session, through_season)
    run = run_elo(games, params)

    scored_inputs = [
        (game, pred)
        for game, pred in zip(games, run.predictions, strict=True)
        if game.fbs_vs_fbs and game.season >= FIRST_SCORED_SEASON and game.id in closing
    ]
    train = [(g, p) for g, p in scored_inputs if TRAIN[0] <= g.season <= TRAIN[1]]
    params = replace(
        params,
        elo_per_point=fit_points_per_elo(
            [p.elo_diff for _, p in train], [g.margin for g, _ in train]
        ),
    )

    scored = [
        ScoredGame(
            season=game.season,
            pred_margin=pred.elo_diff / params.elo_per_point,
            home_win_prob=pred.home_win_prob,
            actual_margin=game.margin,
            market_margin=-closing[game.id],
        )
        for game, pred in scored_inputs
    ]
    periods = [
        summarize_period(f"Train {TRAIN[0]}-{TRAIN[1]}", scored, *TRAIN),
        summarize_period(f"Validate {VALIDATE[0]}-{VALIDATE[1]}", scored, *VALIDATE),
    ]
    if through_season > VALIDATE[1]:
        periods.append(
            summarize_period(f"{through_season} to date", scored, through_season, through_season)
        )
    return EloReport(params, summarize_by_season(scored), periods)
