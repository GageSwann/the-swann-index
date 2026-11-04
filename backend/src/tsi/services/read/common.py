"""Pieces shared by several read models: snapshots, picks, market lines, results."""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from tsi.book.consensus import ConsensusLine, consensus
from tsi.book.grading import clv_points, clv_prob
from tsi.book.odds import prob_from_american
from tsi.db.queries.adjustments import StoredAdjustment, adjustments_by_id
from tsi.db.queries.games import GameRow
from tsi.db.queries.market import closing_snapshots, line_snapshots
from tsi.db.queries.snapshots import PickRow, SnapshotRow


@dataclass(frozen=True)
class PickView:
    market: str  # 'spread' | 'total' | 'ml'
    side: str
    line: float | None
    odds: int
    tier: int
    edge: float
    stake_units: float
    kelly_units: float | None
    result: str | None  # None until graded
    units_won: float | None
    closing_line: float | None
    closing_odds: int | None
    clv: float | None  # points (spread/total) or probability (ml); > 0 beat the close


@dataclass(frozen=True)
class AdjustmentNote:
    """A manual adjustment behind an adjusted prediction (decision #103)."""

    id: int
    team_id: int
    school: str
    off_points: float  # points per game for its offense
    def_points: float  # points per game for its defense
    reason: str


@dataclass(frozen=True)
class RawForecast:
    """The raw model's numbers for a game whose official prediction is adjusted."""

    proj_home: float
    proj_away: float
    spread: float  # home view
    total: float
    home_win_prob: float


@dataclass(frozen=True)
class SnapshotView:
    published_at: datetime
    locked: bool  # the official pre-kickoff snapshot of a game that has started
    proj_home: float
    proj_away: float
    spread: float  # TSI fair spread, home view (negative = home favored)
    total: float
    home_win_prob: float
    sigma_margin: float
    sigma_total: float
    rho: float
    fair_home_ml: int
    fair_away_ml: int
    book_home_ml: int
    book_away_ml: int
    book_spread_home_odds: int
    book_spread_away_odds: int
    book_over_odds: int
    book_under_odds: int
    picks: list[PickView]
    # Manual adjustments (decision #104): the numbers above are then the adjusted ones.
    adjusted: bool
    raw: RawForecast | None  # the raw model's numbers, when adjusted
    adjustments: list[AdjustmentNote]


@dataclass(frozen=True)
class Score:
    home_points: int
    away_points: int
    final: bool


def current_snapshot(
    snaps: Sequence[SnapshotRow], kickoff: datetime | None, now: datetime
) -> tuple[SnapshotRow | None, bool]:
    """(snapshot to show, locked?): the locked one once the game has started, else the latest."""
    if kickoff is not None and kickoff <= now:
        before = [s for s in snaps if s.published_at < kickoff]
        return (before[-1], True) if before else (None, False)
    return (snaps[-1], False) if snaps else (None, False)


def snapshot_view(
    snap: SnapshotRow,
    locked: bool,
    picks: Sequence[PickRow],
    notes: dict[int, AdjustmentNote],
) -> SnapshotView:
    skip = {"adjusted", "raw"}
    fields = {
        k: getattr(snap, k)
        for k in SnapshotView.__dataclass_fields__
        if k not in skip and hasattr(snap, k)
    }
    raw = snap.raw
    return SnapshotView(
        **fields,
        locked=locked,
        picks=[pick_view(p) for p in picks],
        adjusted=snap.adjusted,
        raw=None
        if raw is None
        else RawForecast(raw.proj_home, raw.proj_away, raw.spread, raw.total, raw.home_win_prob),
        adjustments=[notes[i] for i in snap.adjustment_ids or () if i in notes],
    )


def adjustment_notes(session: Session, snaps: Iterable[SnapshotRow]) -> dict[int, AdjustmentNote]:
    """id -> note for every adjustment behind these snapshots (one query, none if unadjusted)."""
    ids = {i for s in snaps for i in s.adjustment_ids or ()}
    return {i: note_of(a) for i, a in adjustments_by_id(session, ids).items()}


def note_of(a: StoredAdjustment) -> AdjustmentNote:
    return AdjustmentNote(a.id, a.team_id, a.school, a.off_points, a.def_points, a.reason)


def pick_view(p: PickRow) -> PickView:
    return PickView(
        market=p.market,
        side=p.side,
        line=p.line_taken,
        odds=p.odds_taken,
        tier=p.tier,
        edge=p.edge,
        stake_units=p.stake_units,
        kelly_units=p.kelly_units,
        result=p.result,
        units_won=p.units_won,
        closing_line=p.closing_line,
        closing_odds=p.closing_odds,
        clv=_clv(p),
    )


def result_of(g: GameRow) -> Score | None:
    if g.home_points is None or g.away_points is None:
        return None
    return Score(g.home_points, g.away_points, g.completed)


def market_lines(
    session: Session, games: Iterable[GameRow], now: datetime
) -> dict[int, ConsensusLine]:
    """Consensus per game: the closing line once kicked off, else the books' lines as of now.

    A started game whose closing lines aren't ingested yet (until the next morning's
    run) falls back to the latest lines on hand, i.e. the last pre-kickoff ones.
    """
    games = list(games)
    started = {g.id for g in games if g.start_time is not None and g.start_time <= now}
    by_game = defaultdict(list)
    if started:
        for snap in closing_snapshots(session, started):
            by_game[snap.game_id].append(snap)
    pending = [g.id for g in games if g.id not in by_game]
    if pending:
        for snap in line_snapshots(session, pending, now):
            by_game[snap.game_id].append(snap)
    return {gid: consensus(snaps) for gid, snaps in by_game.items()}


def _clv(p: PickRow) -> float | None:
    if p.market in ("spread", "total"):
        if p.closing_line is None or p.line_taken is None:
            return None
        return clv_points(p.market, p.side, p.line_taken, p.closing_line)
    if p.closing_odds is None:
        return None
    # Only the picked side's closing price is stored: compare implied probabilities.
    return clv_prob(p.odds_taken, prob_from_american(p.closing_odds))
