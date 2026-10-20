"""Consensus market line across books, and no-vig implied probabilities (doc 05 §3).

- spread / total: median across books (robust to one stale or odd book)
- moneyline: each book's two prices are de-vigged (implied probabilities
  normalized to sum to 1), then averaged; the displayed prices are the medians
"""

import statistics
from collections.abc import Iterable
from dataclasses import dataclass

from tsi.book.odds import prob_from_american
from tsi.db.queries.market import LineSnapshot


@dataclass(frozen=True)
class ConsensusLine:
    spread: float | None  # home view, negative = home favored
    total: float | None
    home_ml: int | None
    away_ml: int | None
    home_prob: float | None  # no-vig P(home wins) implied by the moneylines
    books: int


def no_vig(home_ml: int, away_ml: int) -> tuple[float, float]:
    """Remove the vig from a two-way price: normalize implied probabilities to sum to 1."""
    home, away = prob_from_american(home_ml), prob_from_american(away_ml)
    return home / (home + away), away / (home + away)


def consensus(snapshots: Iterable[LineSnapshot]) -> ConsensusLine:
    """Consensus for ONE game from each book's latest snapshot."""
    snaps = list(snapshots)
    spreads = [s.spread for s in snaps if s.spread is not None]
    totals = [s.total for s in snaps if s.total is not None]
    priced = [s for s in snaps if s.home_ml is not None and s.away_ml is not None]
    return ConsensusLine(
        spread=statistics.median(spreads) if spreads else None,
        total=statistics.median(totals) if totals else None,
        home_ml=round(statistics.median(s.home_ml for s in priced)) if priced else None,
        away_ml=round(statistics.median(s.away_ml for s in priced)) if priced else None,
        home_prob=(
            statistics.fmean(no_vig(s.home_ml, s.away_ml)[0] for s in priced) if priced else None
        ),
        books=len(snaps),
    )
