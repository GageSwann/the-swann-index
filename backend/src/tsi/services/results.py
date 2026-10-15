"""The step shared by the daily and season jobs: games -> stats -> lines.

Order matters: stats and lines attach to games, so games load first.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from tsi.ingest.client import CfbdClient
from tsi.ingest.loaders.games import load_games
from tsi.ingest.loaders.lines import load_lines
from tsi.ingest.loaders.stats import load_team_game_stats


@dataclass(frozen=True)
class ResultsRefresh:
    games: int
    stat_rows: int
    new_line_snapshots: int


def refresh_results(
    client: CfbdClient,
    session_factory: sessionmaker[Session],
    season: int,
    *,
    refresh: bool = False,
) -> ResultsRefresh:
    games = load_games(client, session_factory, season, refresh=refresh)
    stats = load_team_game_stats(client, session_factory, season, refresh=refresh)
    lines = load_lines(client, session_factory, season, refresh=refresh)
    return ResultsRefresh(games.games, stats.rows, lines.inserted)
