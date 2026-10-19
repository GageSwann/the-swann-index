"""Load everything a walk-forward backtest needs, once (all queries up front)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from sqlalchemy.orm import Session

from tsi.backtest.elo_picks import EloPick, elo_picks
from tsi.backtest.splits import is_scored
from tsi.db.queries.market import closing_spreads
from tsi.db.queries.priors import fbs_teams, prior_inputs
from tsi.db.queries.results import GameResult, completed_games
from tsi.db.queries.stats import OffenseRow, offense_rows
from tsi.model.elo import EloParams
from tsi.services.prior_setup import InputsTable, rows_by_season

FIRST_DATA_SEASON = 2014  # supplies 2015's "last season" ratings


@dataclass(frozen=True)
class BacktestData:
    through_season: int
    scored_games: Sequence[GameResult]  # FBS-vs-FBS, closing line, 2015+
    closing: Mapping[int, float]  # game_id -> closing spread
    rows: Mapping[int, Sequence[OffenseRow]]  # season -> team-game rows
    fbs: Mapping[int, set[int]]
    prior_table: InputsTable
    elo: Mapping[int, EloPick]


def load_backtest_data(session: Session, through_season: int) -> BacktestData:
    games = completed_games(session, through_season)
    closing = closing_spreads(session, through_season)
    _, elo = elo_picks(games, closing, EloParams())
    return BacktestData(
        through_season=through_season,
        scored_games=[g for g in games if is_scored(g, closing)],
        closing=closing,
        rows=rows_by_season(offense_rows(session, FIRST_DATA_SEASON, through_season)),
        fbs=fbs_teams(session, FIRST_DATA_SEASON, through_season),
        prior_table=prior_inputs(session, FIRST_DATA_SEASON, through_season),
        elo=elo,
    )
