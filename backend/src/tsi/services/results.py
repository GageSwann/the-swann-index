"""The step shared by the daily and season jobs: games -> stats -> lines.

Order matters: stats and lines attach to games, so games load first. The four CFBD
requests don't depend on each other, so they are fetched concurrently first; the
loaders then read them from the cache in order.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from tsi.ingest.client import CfbdClient
from tsi.ingest.loaders import games as games_loader
from tsi.ingest.loaders import lines as lines_loader
from tsi.ingest.loaders import stats as stats_loader


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
    loaders = (games_loader, stats_loader, lines_loader)
    client.prefetch([r for loader in loaders for r in loader.requests(season)], refresh=refresh)
    games = games_loader.load_games(client, session_factory, season)  # now cached and fresh
    stats = stats_loader.load_team_game_stats(client, session_factory, season)
    lines = lines_loader.load_lines(client, session_factory, season)
    return ResultsRefresh(games.games, stats.rows, lines.inserted)
