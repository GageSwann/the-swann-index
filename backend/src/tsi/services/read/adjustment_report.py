"""Did the manual adjustments help? (doc 04 §11, decision #105)

For every finished game whose locked snapshot was adjusted, score both rows of that
publish against the result: the raw model's and the official adjusted one. Overall,
and per adjustment (each game counts for every adjustment behind it). Only games that
were actually adjusted are compared; elsewhere the two are the same prediction.
"""

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from tsi.db.queries.games import GameRow, season_games
from tsi.db.queries.snapshots import SnapshotRow, snapshots_for_season
from tsi.services.read.common import (
    AdjustmentNote,
    adjustment_notes,
    current_snapshot,
)
from tsi.services.read.common import (
    mean_or_none as mean,
)

SAME = 0.05  # points: closer by less than this counts as no change


@dataclass(frozen=True)
class AdjustedScore:
    """Raw vs. adjusted over a set of adjusted games (lower error is better)."""

    games: int
    raw_mae: float | None  # |predicted margin - actual margin|
    adjusted_mae: float | None
    raw_total_mae: float | None
    adjusted_total_mae: float | None
    raw_su: float | None  # predicted winner won (ties and pick'ems excluded)
    adjusted_su: float | None
    helped: int  # adjusted margin closer to the result
    hurt: int
    same: int


@dataclass(frozen=True)
class AdjustmentScore:
    adjustment: AdjustmentNote
    score: AdjustedScore


@dataclass(frozen=True)
class AdjustmentReport:
    overall: AdjustedScore
    adjustments: list[AdjustmentScore]  # oldest adjustment first


@dataclass(frozen=True)
class _Graded:
    raw: SnapshotRow
    adjusted: SnapshotRow
    margin: int  # actual home margin
    total: int


def season_adjustment_report(session: Session, season: int, now: datetime) -> AdjustmentReport:
    snaps = snapshots_for_season(session, season)
    return adjustment_report(session, season_games(session, season, list(snaps)), snaps, now)


def adjustment_report(
    session: Session,
    games: Iterable[GameRow],
    snaps: Mapping[int, Sequence[SnapshotRow]],
    now: datetime,
) -> AdjustmentReport:
    graded = graded_games(games, snaps, now)
    notes = adjustment_notes(session, [g.adjusted for g in graded])
    by_adjustment: dict[int, list[_Graded]] = defaultdict(list)
    for g in graded:
        for i in g.adjusted.adjustment_ids or ():
            by_adjustment[i].append(g)
    return AdjustmentReport(
        overall=score(graded),
        adjustments=[
            AdjustmentScore(notes[i], score(games))
            for i, games in sorted(by_adjustment.items())
            if i in notes
        ],
    )


def graded_games(
    games: Iterable[GameRow], snaps: Mapping[int, Sequence[SnapshotRow]], now: datetime
) -> list[_Graded]:
    """Finished games whose locked (official) snapshot was adjusted."""
    out = []
    for g in games:
        if not g.completed or g.home_points is None or g.away_points is None:
            continue
        snap, locked = current_snapshot(snaps.get(g.id, []), g.start_time, now)
        if snap is None or not locked or not snap.adjusted or snap.raw is None:
            continue
        margin, total = g.home_points - g.away_points, g.home_points + g.away_points
        out.append(_Graded(snap.raw, snap, margin, total))
    return out


def score(games: Sequence[_Graded]) -> AdjustedScore:
    def margin_err(s: SnapshotRow, g: _Graded) -> float:
        return abs(-s.spread - g.margin)  # spread is home view: margin = -spread

    def total_err(s: SnapshotRow, g: _Graded) -> float:
        return abs(s.total - g.total)

    def winner(s: SnapshotRow, g: _Graded) -> float | None:
        if g.margin == 0 or s.spread == 0:
            return None
        return float((g.margin > 0) == (s.spread < 0))

    gains = [margin_err(g.raw, g) - margin_err(g.adjusted, g) for g in games]
    return AdjustedScore(
        games=len(games),
        raw_mae=mean(margin_err(g.raw, g) for g in games),
        adjusted_mae=mean(margin_err(g.adjusted, g) for g in games),
        raw_total_mae=mean(total_err(g.raw, g) for g in games),
        adjusted_total_mae=mean(total_err(g.adjusted, g) for g in games),
        raw_su=mean(winner(g.raw, g) for g in games),
        adjusted_su=mean(winner(g.adjusted, g) for g in games),
        helped=sum(d >= SAME for d in gains),
        hurt=sum(d <= -SAME for d in gains),
        same=sum(abs(d) < SAME for d in gains),
    )
