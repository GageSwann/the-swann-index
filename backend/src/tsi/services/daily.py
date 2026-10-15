"""Daily refresh of the in-progress season (run by GitHub Actions each night).

Games, advanced stats, and betting lines are re-fetched every day (~4 CFBD calls). Teams and
calendar change rarely mid-season, so they're only loaded the first time a season
appears. Later phases add: refit ratings and publish.
"""

import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import exists, select
from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import CalendarWeek, TeamSeason
from tsi.ingest.client import CfbdClient
from tsi.ingest.freshness import current_season
from tsi.ingest.loaders.calendar import load_calendar
from tsi.ingest.loaders.games import load_games
from tsi.ingest.loaders.lines import load_lines
from tsi.ingest.loaders.stats import load_team_game_stats
from tsi.ingest.loaders.teams import load_teams

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DailyResult:
    season: int
    loaded_teams: bool
    loaded_calendar: bool
    games: int
    stat_rows: int
    new_line_snapshots: int


def run_daily(
    client: CfbdClient, session_factory: sessionmaker[Session], now: datetime
) -> DailyResult:
    season = current_season(now)
    with session_factory() as session:
        has_teams = session.scalar(select(exists().where(TeamSeason.season == season)))
        has_calendar = session.scalar(select(exists().where(CalendarWeek.season == season)))

    if not has_teams:
        load_teams(client, session_factory, season)
    if not has_calendar:
        load_calendar(client, session_factory, season)
    games = load_games(client, session_factory, season)
    stats = load_team_game_stats(client, session_factory, season)
    lines = load_lines(client, session_factory, season)
    logger.info(
        "daily refresh %s: %s games, %s stat rows, %s new line snapshots",
        season,
        games.games,
        stats.rows,
        lines.inserted,
    )
    return DailyResult(
        season, not has_teams, not has_calendar, games.games, stats.rows, lines.inserted
    )
