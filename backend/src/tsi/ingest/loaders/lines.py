"""Load one season of CFBD /lines into market_lines as change-only snapshots (1 call)."""

from dataclasses import dataclass
from itertools import batched

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import Game, MarketLine
from tsi.db.upsert import CHUNK_SIZE
from tsi.ingest.client import CfbdClient
from tsi.ingest.transform.lines import (
    VALUE_FIELDS,
    LineKey,
    StoredLine,
    line_snapshots,
    plan_line_changes,
)


@dataclass(frozen=True)
class LinesLoadResult:
    season: int
    inserted: int
    marked_closing: int
    unchanged: int


def load_lines(
    client: CfbdClient,
    session_factory: sessionmaker[Session],
    season: int,
    *,
    refresh: bool = False,
) -> LinesLoadResult:
    response = client.get_response("/lines", {"year": season}, refresh=refresh)
    snapshots = line_snapshots(response.data)
    with session_factory.begin() as session:
        kickoff = dict(
            session.execute(select(Game.id, Game.start_time).where(Game.season == season))
            .tuples()
            .all()
        )
        plan = plan_line_changes(
            snapshots, _latest_lines(session, season), kickoff, response.fetched_at
        )
        for chunk in batched(plan.inserts, CHUNK_SIZE):
            session.execute(insert(MarketLine).values(list(chunk)).on_conflict_do_nothing())
        if plan.mark_closing:
            session.execute(
                update(MarketLine)
                .where(MarketLine.id.in_(plan.mark_closing))
                .values(is_closing=True)
            )
    unchanged = len(snapshots) - len(plan.inserts) - len(plan.mark_closing)
    return LinesLoadResult(season, len(plan.inserts), len(plan.mark_closing), unchanged)


def _latest_lines(session: Session, season: int) -> dict[LineKey, StoredLine]:
    columns = [getattr(MarketLine, f) for f in VALUE_FIELDS]
    query = (
        select(
            MarketLine.id, MarketLine.game_id, MarketLine.provider, MarketLine.is_closing, *columns
        )
        .join(Game, Game.id == MarketLine.game_id)
        .where(Game.season == season)
        .order_by(MarketLine.game_id, MarketLine.provider, MarketLine.fetched_at.desc())
        .distinct(MarketLine.game_id, MarketLine.provider)  # Postgres DISTINCT ON: newest row
    )
    return {
        (row.game_id, row.provider): StoredLine(row.id, tuple(row[4:]), row.is_closing)
        for row in session.execute(query)
    }
