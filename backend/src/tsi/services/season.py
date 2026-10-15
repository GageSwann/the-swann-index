"""Load everything for one season, in dependency order (~9 CFBD calls; 0 if cached).

Order matters: teams (and their venues) before games, games before stats/lines,
since those rows point at games. Venues load once, when the table is empty.
Every step is idempotent, so a failed run can simply be re-run.
"""

import logging
from dataclasses import dataclass

from sqlalchemy import exists, select
from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import Venue
from tsi.ingest.client import CfbdClient
from tsi.ingest.loaders.calendar import load_calendar
from tsi.ingest.loaders.games import load_games
from tsi.ingest.loaders.lines import load_lines
from tsi.ingest.loaders.priors import load_prior_inputs
from tsi.ingest.loaders.stats import load_team_game_stats
from tsi.ingest.loaders.teams import load_teams
from tsi.ingest.loaders.venues import load_venues

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SeasonResult:
    season: int
    teams: int
    calendar_weeks: int
    games: int
    stat_rows: int
    new_line_snapshots: int
    priors_talent: int
    priors_returning: int

    def summary(self) -> str:
        return (
            f"{self.season}: {self.teams} teams, {self.calendar_weeks} weeks, {self.games} games, "
            f"{self.stat_rows} stat rows, {self.new_line_snapshots} new line snapshots, "
            f"priors {self.priors_talent} talent / {self.priors_returning} returning"
        )


def run_season(
    client: CfbdClient,
    session_factory: sessionmaker[Session],
    season: int,
    *,
    refresh: bool = False,
) -> SeasonResult:
    with session_factory() as session:
        has_venues = session.scalar(select(exists().select_from(Venue)))
    if not has_venues:
        load_venues(client, session_factory, refresh=refresh)

    teams = load_teams(client, session_factory, season, refresh=refresh)
    weeks = load_calendar(client, session_factory, season, refresh=refresh)
    games = load_games(client, session_factory, season, refresh=refresh)
    stats = load_team_game_stats(client, session_factory, season, refresh=refresh)
    lines = load_lines(client, session_factory, season, refresh=refresh)
    priors = load_prior_inputs(client, session_factory, season, refresh=refresh)

    result = SeasonResult(
        season,
        teams.teams,
        weeks,
        games.games,
        stats.rows,
        lines.inserted,
        priors.talent,
        priors.returning,
    )
    logger.info("season %s", result.summary())
    return result
