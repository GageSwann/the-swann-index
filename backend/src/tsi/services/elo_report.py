"""Run Elo over every completed game and score it against the closing line.

Elo itself is walk-forward (each prediction uses only earlier games). The one
fitted number, points per Elo, is fit on the TRAIN seasons only and then applied
everywhere, so the validation seasons stay out-of-sample.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.orm import Session

from tsi.backtest.elo_picks import elo_picks
from tsi.backtest.evaluate import ScoredGame, Summary, summarize_by_season, summarize_period
from tsi.backtest.splits import TRAIN, VALIDATE, is_scored
from tsi.db.queries.market import closing_spreads
from tsi.db.queries.results import completed_games
from tsi.model.elo import EloParams


@dataclass(frozen=True)
class EloReport:
    params: EloParams
    seasons: list[Summary]
    periods: list[Summary]


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
