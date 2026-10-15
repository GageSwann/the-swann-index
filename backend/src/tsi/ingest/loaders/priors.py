"""Load one season's preseason prior inputs (talent + returning production; 2 calls)."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import Prior, Team
from tsi.db.upsert import upsert_rows
from tsi.ingest.client import CfbdClient
from tsi.ingest.transform.priors import returning_rows, talent_rows


@dataclass(frozen=True)
class PriorsLoadResult:
    season: int
    talent: int
    returning: int
    unmatched: int  # CFBD team names not found in `teams`


def load_prior_inputs(
    client: CfbdClient,
    session_factory: sessionmaker[Session],
    season: int,
    *,
    refresh: bool = False,
) -> PriorsLoadResult:
    talent_raw = client.get("/talent", {"year": season}, refresh=refresh)
    returning_raw = client.get("/player/returning", {"year": season}, refresh=refresh)
    with session_factory.begin() as session:
        team_ids = dict(session.execute(select(Team.school, Team.id)).tuples().all())
        talent = talent_rows(talent_raw, season, team_ids)
        returning = returning_rows(returning_raw, season, team_ids)
        upsert_rows(session, Prior, talent)
        upsert_rows(session, Prior, returning)
    unmatched = len(talent_raw) + len(returning_raw) - len(talent) - len(returning)
    return PriorsLoadResult(season, len(talent), len(returning), unmatched)
