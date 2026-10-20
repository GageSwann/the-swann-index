"""Today's board: every upcoming game forecast, priced, compared with the market, picked.

forecast (services/predict.py) -> TSI Book prices (book/pricing.py)
-> consensus market line as of now (book/consensus.py) -> shrunk edges
(book/edges.py) -> TSI Plays (book/picks.py). Read-only: nothing is written here.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from tsi.book.config import BookConfig
from tsi.book.consensus import ConsensusLine, consensus
from tsi.book.edges import GameEdges, game_edges
from tsi.book.picks import PickDecision, PickRules, choose_picks
from tsi.book.pricing import GameMarkets, price_game
from tsi.db.queries.market import line_snapshots
from tsi.db.queries.schedule import upcoming_games
from tsi.db.queries.teams import team_names
from tsi.ingest.freshness import current_season
from tsi.model.artifact import ModelArtifact
from tsi.services.live_inputs import LiveInputs, load_live_inputs
from tsi.services.predict import GameForecast, forecast_games

DEFAULT_DAYS = 8  # a full week of games ahead
SEASON_DAYS = 200  # window when a specific week is asked for


@dataclass(frozen=True)
class BoardGame:
    forecast: GameForecast
    markets: GameMarkets
    market: ConsensusLine
    edges: GameEdges
    picks: list[PickDecision]


@dataclass(frozen=True)
class Board:
    games: list[BoardGame]
    names: dict[int, str]  # team id -> school, for display


def build_board(
    session: Session,
    now: datetime,
    artifact: ModelArtifact,
    days: int = DEFAULT_DAYS,
    book: BookConfig | None = None,
    rules: PickRules | None = None,
    week: tuple[str, int] | None = None,  # (season_type, week): only that week's games
    live: LiveInputs | None = None,  # reuse inputs already loaded for the same moment
) -> Board:
    season = current_season(now)
    window = SEASON_DAYS if week else days
    upcoming = upcoming_games(session, now, now + timedelta(days=window))
    games = [
        g
        for g in upcoming
        if g.season == season and (week is None or (g.season_type, g.week) == week)
    ]
    if not games:
        return Board([], {})
    live = live or load_live_inputs(session, season, now, artifact)
    snaps = defaultdict(list)
    for snap in line_snapshots(session, [g.id for g in games], now):
        snaps[snap.game_id].append(snap)

    board: list[BoardGame] = []
    for forecast in forecast_games(games, live, artifact):
        dist = forecast.distribution
        market = consensus(snaps[forecast.game.id])
        edges = game_edges(dist, market, artifact.edge_shrink)
        board.append(
            BoardGame(forecast, price_game(dist, book), market, edges, choose_picks(edges, rules))
        )
    names = team_names(session, {t for g in games for t in (g.home_id, g.away_id)})
    return Board(board, names)
