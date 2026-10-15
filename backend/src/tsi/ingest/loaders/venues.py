"""Load all venues from CFBD /venues (one call, no season)."""

from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import Venue
from tsi.db.upsert import upsert_rows
from tsi.ingest.client import CfbdClient
from tsi.ingest.transform.venues import venue_rows


def load_venues(
    client: CfbdClient, session_factory: sessionmaker[Session], *, refresh: bool = False
) -> int:
    rows = venue_rows(client.get("/venues", refresh=refresh))
    with session_factory.begin() as session:
        return upsert_rows(session, Venue, rows)
