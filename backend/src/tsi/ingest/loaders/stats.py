"""Load one season of CFBD advanced game stats into team_game_stats (2 calls per season).

Run after `games` for the same season: stats rows are matched to our games.
"""

from dataclasses import dataclass

from sqlalchemy import select, union_all
from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import Game, Team, TeamGameStats
from tsi.db.upsert import upsert_rows
from tsi.ingest.client import CfbdClient
from tsi.ingest.transform.stats import GameIndex, team_game_stat_rows

ENDPOINT = "/stats/game/advanced"


@dataclass(frozen=True)
class StatsLoadResult:
    season: int
    rows: int
    unmatched: int  # CFBD rows whose game/team isn't in our tables


def load_team_game_stats(
    client: CfbdClient,
    session_factory: sessionmaker[Session],
    season: int,
    *,
    refresh: bool = False,
) -> StatsLoadResult:
    filtered = client.get(ENDPOINT, {"year": season, "excludeGarbageTime": "true"}, refresh=refresh)
    full = client.get(ENDPOINT, {"year": season}, refresh=refresh)
    with session_factory.begin() as session:
        rows = team_game_stat_rows(filtered, full, _game_index(session, season))
        count = upsert_rows(session, TeamGameStats, rows)
    return StatsLoadResult(season, count, len(filtered) - len(rows))


def _game_index(session: Session, season: int) -> GameIndex:
    home = select(Game.id, Team.school, Team.id, Game.home_points).join(
        Team, Team.id == Game.home_id
    )
    away = select(Game.id, Team.school, Team.id, Game.away_points).join(
        Team, Team.id == Game.away_id
    )
    sides = union_all(home.where(Game.season == season), away.where(Game.season == season))
    index: dict[int, dict[str, tuple[int, int | None]]] = {}
    for game_id, school, team_id, points in session.execute(sides):
        index.setdefault(game_id, {})[school] = (team_id, points)
    return index
