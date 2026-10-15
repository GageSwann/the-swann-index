"""Load roster-change prior inputs for one season: recruiting, portal, head-coach change.

Calls (all cached forever once a season is over): recruiting classes Y-3..Y (4),
portal Y (1), coaches Y and Y-1 (2). Each source fills only its own `priors` column.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import Prior, Team
from tsi.db.upsert import upsert_rows
from tsi.ingest.client import CfbdClient
from tsi.ingest.transform.roster import (
    RECRUITING_CLASSES,
    coach_changes,
    portal_net,
    preseason_coaches,
    recruiting_average,
)


@dataclass(frozen=True)
class RosterLoadResult:
    season: int
    recruiting: int
    portal: int
    coach_flags: int


def load_roster_inputs(
    client: CfbdClient,
    session_factory: sessionmaker[Session],
    season: int,
    *,
    refresh: bool = False,
) -> RosterLoadResult:
    classes = {
        year: client.get("/recruiting/teams", {"year": year}, refresh=refresh)
        for year in range(season - RECRUITING_CLASSES + 1, season + 1)
    }
    portal_raw = client.get("/player/portal", {"year": season}, refresh=refresh)
    coaches_now = client.get("/coaches", {"year": season}, refresh=refresh)
    coaches_before = client.get("/coaches", {"year": season - 1}, refresh=refresh)

    with session_factory.begin() as session:
        team_ids = {school: tid for school, tid in session.execute(select(Team.school, Team.id))}
        known = set(team_ids.values())
        recruiting = recruiting_average(classes, season, team_ids)
        portal = portal_net(portal_raw, season, team_ids)
        changes = coach_changes(
            preseason_coaches(coaches_now, season), preseason_coaches(coaches_before, season - 1)
        )
        upsert_rows(session, Prior, _rows(season, recruiting, "recruiting_points"))
        upsert_rows(session, Prior, _rows(season, portal, "portal_net"))
        upsert_rows(
            session,
            Prior,
            _rows(season, {t: v for t, v in changes.items() if t in known}, "new_head_coach"),
        )
    return RosterLoadResult(season, len(recruiting), len(portal), len(changes))


def _rows(season: int, values: dict[int, object], column: str) -> list[dict[str, object]]:
    return [{"season": season, "team_id": team, column: value} for team, value in values.items()]
