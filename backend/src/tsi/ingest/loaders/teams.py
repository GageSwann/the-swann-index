"""Load one season of CFBD /teams into venues, teams, and team_seasons.

Team identity (name, colors, logo) is only overwritten when loading the newest
season seen so far, so backfilling 2014 never replaces current branding.
Older seasons still insert teams that no longer exist today.
"""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import Team, TeamSeason, Venue
from tsi.db.upsert import upsert_rows
from tsi.ingest.client import CfbdClient
from tsi.ingest.transform.teams import team_rows, team_season_rows, team_venues
from tsi.ingest.transform.venues import venue_rows


@dataclass(frozen=True)
class TeamsLoadResult:
    season: int
    teams: int
    team_seasons: int
    identity_updated: bool


def load_teams(
    client: CfbdClient,
    session_factory: sessionmaker[Session],
    season: int,
    *,
    refresh: bool = False,
) -> TeamsLoadResult:
    raw = client.get("/teams", {"year": season}, refresh=refresh)
    with session_factory.begin() as session:
        newest = session.scalar(select(func.max(TeamSeason.season)))
        update_identity = newest is None or season >= newest
        # Venues first so teams.venue_id always points at an existing row.
        upsert_rows(session, Venue, venue_rows(team_venues(raw)), update=False)
        teams = upsert_rows(session, Team, team_rows(raw), update=update_identity)
        seasons = upsert_rows(session, TeamSeason, team_season_rows(raw, season))
    return TeamsLoadResult(season, teams, seasons, update_identity)
