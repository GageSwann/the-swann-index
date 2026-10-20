"""Grade official picks after the final: result, units, and the closing line for CLV.

Only picks on each game's locked snapshot (latest published before kickoff) are
graded; picks on superseded snapshots never count. Grading fills the pick's
result columns; the prediction row itself is never touched (rule 2).
Closing line = consensus of the books' closing snapshots (median spread/total,
median moneyline prices for moneyline picks).
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.orm import Session, sessionmaker

from tsi.book.consensus import ConsensusLine, consensus
from tsi.book.grading import grade_pick
from tsi.db.models import Pick
from tsi.db.queries.market import closing_snapshots
from tsi.db.queries.predictions import LockedPick, ungraded_locked_picks


@dataclass(frozen=True)
class GradeResult:
    graded: int
    wins: int
    losses: int
    pushes: int
    units: float


def grade_picks(session_factory: sessionmaker[Session], now: datetime) -> GradeResult:
    with session_factory.begin() as session:
        picks = ungraded_locked_picks(session)
        closing = _closing_lines(session, {p.game_id for p in picks})
        rows = [_graded_row(p, closing.get(p.game_id), now) for p in picks]
        if rows:
            session.execute(update(Pick), rows)
    results = [r["result"] for r in rows]
    return GradeResult(
        graded=len(rows),
        wins=results.count("win"),
        losses=results.count("loss"),
        pushes=results.count("push"),
        units=sum(r["units_won"] for r in rows),
    )


def _graded_row(p: LockedPick, close: ConsensusLine | None, now: datetime) -> dict:
    grade = grade_pick(
        p.market, p.side, p.line_taken, p.odds_taken, p.home_points, p.away_points, p.stake_units
    )
    closing_line = closing_odds = None
    if close is not None:
        if p.market == "spread":
            closing_line = close.spread
        elif p.market == "total":
            closing_line = close.total
        else:
            closing_odds = close.home_ml if p.side == "home" else close.away_ml
    return {
        "id": p.pick_id,
        "result": grade.result,
        "units_won": grade.units_won,
        "closing_line": closing_line,
        "closing_odds": closing_odds,
        "graded_at": now,
    }


def _closing_lines(session: Session, game_ids: set[int]) -> dict[int, ConsensusLine]:
    by_game = defaultdict(list)
    for snap in closing_snapshots(session, game_ids):
        by_game[snap.game_id].append(snap)
    return {gid: consensus(snaps) for gid, snaps in by_game.items()}
