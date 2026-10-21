"""Published prediction snapshots and their picks, read in full for the API.

(Grading and de-duplication use the narrower queries in `predictions.py`.)
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import Game, Pick, Prediction

RAW = "raw"


@dataclass(frozen=True)
class SnapshotRow:
    id: int
    game_id: int
    published_at: datetime
    proj_home: float
    proj_away: float
    spread: float  # fair, home view
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


@dataclass(frozen=True)
class PickRow:
    id: int
    prediction_id: int
    market: str
    side: str
    line_taken: float | None
    odds_taken: int
    edge: float
    tier: int
    stake_units: float
    kelly_units: float | None
    closing_line: float | None
    closing_odds: int | None
    result: str | None
    units_won: float | None
    graded_at: datetime | None


SNAPSHOT_COLUMNS = (
    Prediction.id,
    Prediction.game_id,
    Prediction.published_at,
    Prediction.proj_home,
    Prediction.proj_away,
    Prediction.spread,
    Prediction.total,
    Prediction.home_win_prob,
    Prediction.sigma_margin,
    Prediction.sigma_total,
    Prediction.rho,
    Prediction.fair_home_ml,
    Prediction.fair_away_ml,
    Prediction.book_home_ml,
    Prediction.book_away_ml,
    Prediction.book_spread_home_odds,
    Prediction.book_spread_away_odds,
    Prediction.book_over_odds,
    Prediction.book_under_odds,
)


def snapshots_for_games(session: Session, game_ids: Iterable[int]) -> dict[int, list[SnapshotRow]]:
    """game id -> every raw snapshot, oldest first."""
    query = (
        select(*SNAPSHOT_COLUMNS)
        .where(Prediction.game_id.in_(list(game_ids)), Prediction.variant == RAW)
        .order_by(Prediction.game_id, Prediction.published_at, Prediction.id)
    )
    out: dict[int, list[SnapshotRow]] = defaultdict(list)
    for row in session.execute(query):
        snap = SnapshotRow(*row)
        out[snap.game_id].append(snap)
    return out


def snapshots_for_season(session: Session, season: int) -> dict[int, list[SnapshotRow]]:
    """Every raw snapshot of a season's games (the ledger and live report)."""
    query = (
        select(*SNAPSHOT_COLUMNS)
        .join(Game, Game.id == Prediction.game_id)
        .where(Game.season == season, Prediction.variant == RAW)
        .order_by(Prediction.game_id, Prediction.published_at, Prediction.id)
    )
    out: dict[int, list[SnapshotRow]] = defaultdict(list)
    for row in session.execute(query):
        snap = SnapshotRow(*row)
        out[snap.game_id].append(snap)
    return out


def picks_for_snapshots(
    session: Session, prediction_ids: Iterable[int]
) -> dict[int, list[PickRow]]:
    query = select(
        Pick.id,
        Pick.prediction_id,
        Pick.market,
        Pick.side,
        Pick.line_taken,
        Pick.odds_taken,
        Pick.edge,
        Pick.tier,
        Pick.stake_units,
        Pick.kelly_units,
        Pick.closing_line,
        Pick.closing_odds,
        Pick.result,
        Pick.units_won,
        Pick.graded_at,
    ).where(Pick.prediction_id.in_(list(prediction_ids)))
    out: dict[int, list[PickRow]] = defaultdict(list)
    for row in session.execute(query):
        pick = PickRow(*row)
        out[pick.prediction_id].append(pick)
    return out
