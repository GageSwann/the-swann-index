"""Load one season of CFBD /lines into market_lines as change-only snapshots (1 call)."""

from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import distinct_on, insert
from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import Game, MarketLine
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
    skipped: int  # lines for games not in our games table


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
        games = select(Game.id, Game.start_time).where(Game.season == season)
        kickoff = {game_id: start for game_id, start in session.execute(games)}
        plan = plan_line_changes(
            snapshots, _latest_lines(session, season), kickoff, response.fetched_at
        )
        if plan.inserts:
            session.execute(insert(MarketLine).on_conflict_do_nothing(), plan.inserts)
        if plan.mark_closing:
            session.execute(
                update(MarketLine)
                .where(MarketLine.id.in_(plan.mark_closing))
                .values(is_closing=True)
            )
    return LinesLoadResult(
        season, len(plan.inserts), len(plan.mark_closing), plan.unchanged, plan.skipped
    )


def _latest_lines(session: Session, season: int) -> dict[LineKey, StoredLine]:
    columns = [getattr(MarketLine, f) for f in VALUE_FIELDS]
    query = (
        select(
            MarketLine.id, MarketLine.game_id, MarketLine.provider, MarketLine.is_closing, *columns
        )
        .join(Game, Game.id == MarketLine.game_id)
        .where(Game.season == season)
        .order_by(MarketLine.game_id, MarketLine.provider, MarketLine.fetched_at.desc())
        .ext(distinct_on(MarketLine.game_id, MarketLine.provider))  # newest row per key
    )
    return {
        (row.game_id, row.provider): StoredLine(row.id, tuple(row[4:]), row.is_closing)
        for row in session.execute(query)
    }
