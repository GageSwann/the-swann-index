"""Published prediction snapshots: the latest per game, and the locked (pre-kickoff) one.

The locked snapshot is derived, never flagged: the latest prediction with
`published_at < games.start_time` (rule 2), the `adjusted` row when that publish had
one (decision #104). Only its picks are official.
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from tsi.db.models import Game, Pick, Prediction
from tsi.db.queries.filters import one_of

RAW = "raw"
ADJUSTED = "adjusted"
# Within one publish, the adjusted row is the official one: 'adjusted' sorts before 'raw'.
OFFICIAL_FIRST = Prediction.variant.asc()


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

    prediction: tuple[float | int, ...]  # the raw row
    picks: frozenset[PickKey]
    adjusted: tuple[float | int, ...] | None = None  # the adjusted row, if any
    adjustment_ids: tuple[int, ...] = ()


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
    """What each game's latest publish said: its raw row, adjusted row (if any) and picks."""
    latest_at = (
        select(Prediction.game_id, func.max(Prediction.published_at).label("at"))
        .where(one_of(Prediction.game_id, game_ids))
        .group_by(Prediction.game_id)
        .subquery()
    )
    latest = select(
        Prediction.id, Prediction.game_id, Prediction.variant, Prediction.adjustment_ids,
        *FINGERPRINT,
    ).join(
        latest_at,
        (latest_at.c.game_id == Prediction.game_id) & (latest_at.c.at == Prediction.published_at),
    )  # fmt: skip
    rows = list(session.execute(latest))
    picks: dict[int, set[PickKey]] = defaultdict(set)
    query = select(
        Pick.prediction_id, Pick.market, Pick.side, Pick.line_taken, Pick.odds_taken, Pick.tier
    ).where(one_of(Pick.prediction_id, [r[0] for r in rows]))
    for pid, market, side, line, odds, tier in session.execute(query):
        picks[pid].add(PickKey(market, side, line, odds, tier))

    by_game: dict[int, dict[str, tuple]] = defaultdict(dict)
    for pid, gid, variant, ids, *values in rows:
        by_game[gid][variant] = (pid, fingerprint(values), tuple(ids or ()))
    out = {}
    for gid, variants in by_game.items():
        raw, adj = variants.get(RAW), variants.get(ADJUSTED)
        official = adj or raw
        out[gid] = SnapshotKey(
            raw[1] if raw else (),
            frozenset(picks[official[0]]),
            adj[1] if adj else None,
            adj[2] if adj else (),
        )
    return out


def locked_snapshot_ids():
    """Subquery: (game_id, prediction id) of each game's locked snapshot."""
    query = (
        select(Prediction.game_id, Prediction.id.label("prediction_id"))
        .join(Game, Game.id == Prediction.game_id)
        .where(Prediction.published_at < Game.start_time)
        .order_by(
            Prediction.game_id, Prediction.published_at.desc(), OFFICIAL_FIRST, Prediction.id.desc()
        )
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
