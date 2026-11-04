"""Published prediction snapshots and their picks, read in full for the API.

(Grading and de-duplication use the narrower queries in `predictions.py`.)
Each publish of a game is one `SnapshotRow`: the official row (`adjusted` when the game
had manual adjustments, decision #104) with the raw model's row attached as `raw`.
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import Game, Pick, Prediction
from tsi.db.queries.filters import one_of
from tsi.db.queries.predictions import ADJUSTED, OFFICIAL_FIRST


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
    variant: str = "raw"
    adjustment_ids: list[int] | None = None
    raw: "SnapshotRow | None" = None  # the raw model's row of the same publish, if adjusted

    @property
    def adjusted(self) -> bool:
        return self.variant == ADJUSTED


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
    Prediction.variant,
    Prediction.adjustment_ids,
)
ORDER = (Prediction.game_id, Prediction.published_at, OFFICIAL_FIRST, Prediction.id)


def _by_game(rows: Iterable) -> dict[int, list[SnapshotRow]]:
    """Fold each publish's rows (official first) into one SnapshotRow per publish."""
    out: dict[int, list[SnapshotRow]] = defaultdict(list)
    for row in rows:
        snap = SnapshotRow(*row)
        snaps = out[snap.game_id]
        last = snaps[-1] if snaps else None
        if last is not None and last.published_at == snap.published_at:
            snaps[-1] = replace(last, raw=snap)  # the raw twin of an adjusted row
        else:
            snaps.append(snap)
    return out


def snapshots_for_games(session: Session, game_ids: Iterable[int]) -> dict[int, list[SnapshotRow]]:
    """game id -> every snapshot, oldest first."""
    query = select(*SNAPSHOT_COLUMNS).where(one_of(Prediction.game_id, game_ids)).order_by(*ORDER)
    return _by_game(session.execute(query))


def snapshots_for_season(session: Session, season: int) -> dict[int, list[SnapshotRow]]:
    """Every snapshot of a season's games (the ledger and live report)."""
    query = (
        select(*SNAPSHOT_COLUMNS)
        .join(Game, Game.id == Prediction.game_id)
        .where(Game.season == season)
        .order_by(*ORDER)
    )
    return _by_game(session.execute(query))


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
    ).where(one_of(Pick.prediction_id, prediction_ids))
    out: dict[int, list[PickRow]] = defaultdict(list)
    for row in session.execute(query):
        pick = PickRow(*row)
        out[pick.prediction_id].append(pick)
    return out
