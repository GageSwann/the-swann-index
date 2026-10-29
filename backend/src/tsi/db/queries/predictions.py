"""Published prediction snapshots: the latest per game, and the locked (pre-kickoff) one.

The locked snapshot is derived, never flagged: the latest `raw` prediction with
`published_at < games.start_time` (rule 2). Only its picks are official.
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from tsi.db.models import Game, Pick, Prediction
from tsi.db.queries.filters import one_of

RAW = "raw"


@dataclass(frozen=True)
class PickKey:
    market: str
    side: str
    line: float | None
    odds: int
    tier: int


@dataclass(frozen=True)
class SnapshotKey:
    """What a snapshot said; a new one is published only when this changes."""

    prediction: tuple[float | int, ...]
    picks: frozenset[PickKey]


@dataclass(frozen=True)
class LockedPick:
    pick_id: int
    game_id: int
    market: str
    side: str
    line_taken: float | None
    odds_taken: int
    stake_units: float
    home_points: int
    away_points: int


FINGERPRINT = (
    Prediction.proj_home,
    Prediction.proj_away,
    Prediction.sigma_margin,
    Prediction.sigma_total,
    Prediction.rho,
    Prediction.book_home_ml,
    Prediction.book_away_ml,
)


def fingerprint(values: Iterable[float | int]) -> tuple[float | int, ...]:
    return tuple(round(v, 2) if isinstance(v, float) else v for v in values)


def latest_snapshots(session: Session, game_ids: Iterable[int]) -> dict[int, SnapshotKey]:
    latest = (
        select(Prediction.id, Prediction.game_id, *FINGERPRINT)
        .where(one_of(Prediction.game_id, game_ids), Prediction.variant == RAW)
        .order_by(Prediction.game_id, Prediction.published_at.desc(), Prediction.id.desc())
        .ext(postgresql.distinct_on(Prediction.game_id))
    )
    rows = {pid: (gid, fingerprint(values)) for pid, gid, *values in session.execute(latest)}
    picks: dict[int, set[PickKey]] = defaultdict(set)
    query = select(
        Pick.prediction_id, Pick.market, Pick.side, Pick.line_taken, Pick.odds_taken, Pick.tier
    ).where(one_of(Pick.prediction_id, rows))
    for pid, market, side, line, odds, tier in session.execute(query):
        picks[pid].add(PickKey(market, side, line, odds, tier))
    return {gid: SnapshotKey(fp, frozenset(picks[pid])) for pid, (gid, fp) in rows.items()}


def locked_snapshot_ids():
    """Subquery: (game_id, prediction id) of each game's locked snapshot."""
    query = (
        select(Prediction.game_id, Prediction.id.label("prediction_id"))
        .join(Game, Game.id == Prediction.game_id)
        .where(Prediction.variant == RAW, Prediction.published_at < Game.start_time)
        .order_by(Prediction.game_id, Prediction.published_at.desc(), Prediction.id.desc())
        .ext(postgresql.distinct_on(Prediction.game_id))
    )
    return query.subquery()


def ungraded_locked_picks(session: Session) -> list[LockedPick]:
    """Official picks (from locked snapshots) of completed games that are not graded yet."""
    locked = locked_snapshot_ids()
    query = (
        select(
            Pick.id,
            Game.id,
            Pick.market,
            Pick.side,
            Pick.line_taken,
            Pick.odds_taken,
            Pick.stake_units,
            Game.home_points,
            Game.away_points,
        )
        .join(locked, locked.c.prediction_id == Pick.prediction_id)
        .join(Game, Game.id == locked.c.game_id)
        .where(
            Pick.result.is_(None),
            Game.completed,
            Game.home_points.is_not(None),
            Game.away_points.is_not(None),
        )
    )
    return [LockedPick(*row) for row in session.execute(query)]
