"""Load one season of CFBD /games (regular + postseason) into games.

Unknown opponents get placeholder teams first so every foreign key resolves.
Team seasons from game records only fill gaps; /teams data always wins.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import Game, Team, TeamSeason
from tsi.db.upsert import upsert_rows
from tsi.ingest.client import CfbdClient
from tsi.ingest.transform.games import game_rows, participant_team_seasons, placeholder_teams


@dataclass(frozen=True)
class GamesLoadResult:
    season: int
    games: int
    placeholder_teams: int


def load_games(
    client: CfbdClient,
    session_factory: sessionmaker[Session],
    season: int,
    *,
    refresh: bool = False,
) -> GamesLoadResult:
    raw = client.get("/games", {"year": season, "seasonType": "both"}, refresh=refresh)
    with session_factory.begin() as session:
        known = set(session.scalars(select(Team.id)))
        placeholders = placeholder_teams(raw, known)
        upsert_rows(session, Team, placeholders, update=False)
        upsert_rows(session, TeamSeason, participant_team_seasons(raw), update=False)
        games = upsert_rows(session, Game, game_rows(raw))
    return GamesLoadResult(season, games, len(placeholders))
