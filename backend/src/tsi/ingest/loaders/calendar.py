"""Load one season of CFBD /calendar into calendar_weeks."""

from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import CalendarWeek
from tsi.db.upsert import upsert_rows
from tsi.ingest.client import CfbdClient
from tsi.ingest.transform.calendar import calendar_rows


def load_calendar(
    client: CfbdClient,
    session_factory: sessionmaker[Session],
    season: int,
    *,
    refresh: bool = False,
) -> int:
    rows = calendar_rows(client.get("/calendar", {"year": season}, refresh=refresh))
    with session_factory.begin() as session:
        return upsert_rows(session, CalendarWeek, rows)
