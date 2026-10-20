"""Market lines: closing and opening consensus (backtests) and live snapshots (publishing).

Every consensus is the median across sportsbooks, aggregator feeds excluded, so backtests
and live grading measure against the same number.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from tsi.db.models import Game, MarketLine

AGGREGATORS = ("consensus", "teamrankings")  # CFBD "providers" that are not sportsbooks


@dataclass(frozen=True)
class OpeningLine:
    spread: float | None  # median opener across books, home view
    total: float | None


@dataclass(frozen=True)
class LineSnapshot:
    """One book's line for a game as of some moment (its latest change at or before it)."""

    game_id: int
    provider: str
    spread: float | None
    total: float | None
    home_ml: int | None
    away_ml: int | None
    fetched_at: datetime


def closing_spreads(session: Session, through_season: int) -> dict[int, float]:
    """game_id -> median closing spread across books (home view, negative = home favored)."""
    return _closing_median(session, MarketLine.spread, through_season)


def closing_totals(session: Session, through_season: int) -> dict[int, float]:
    """game_id -> median closing over/under total across books (points)."""
    return _closing_median(session, MarketLine.total, through_season)


def opening_lines(session: Session, through_season: int) -> dict[int, OpeningLine]:
    """game_id -> median opening spread/total across books (some books' openers are stale)."""
    median = lambda col: func.percentile_cont(0.5).within_group(col)  # noqa: E731
    query = (
        select(MarketLine.game_id, median(MarketLine.spread_open), median(MarketLine.total_open))
        .join(Game, Game.id == MarketLine.game_id)
        .where(
            MarketLine.is_closing,
            MarketLine.provider.not_in(AGGREGATORS),
            Game.season <= through_season,
        )
        .group_by(MarketLine.game_id)
    )
    return {
        gid: OpeningLine(_float(spread), _float(total))
        for gid, spread, total in session.execute(query)
        if spread is not None or total is not None
    }


def line_snapshots(
    session: Session, game_ids: Iterable[int], as_of: datetime
) -> list[LineSnapshot]:
    """Each book's latest line for each game fetched at or before `as_of`."""
    query = (
        select(
            MarketLine.game_id,
            MarketLine.provider,
            MarketLine.spread,
            MarketLine.total,
            MarketLine.home_ml,
            MarketLine.away_ml,
            MarketLine.fetched_at,
        )
        .where(
            MarketLine.game_id.in_(list(game_ids)),
            MarketLine.fetched_at <= as_of,
            MarketLine.provider.not_in(AGGREGATORS),
        )
        .order_by(MarketLine.game_id, MarketLine.provider, MarketLine.fetched_at.desc())
        .ext(postgresql.distinct_on(MarketLine.game_id, MarketLine.provider))
    )
    return [LineSnapshot(*row) for row in session.execute(query)]


def closing_snapshots(session: Session, game_ids: Iterable[int]) -> list[LineSnapshot]:
    """Each book's closing line (captured at/after kickoff) for each game."""
    query = (
        select(
            MarketLine.game_id,
            MarketLine.provider,
            MarketLine.spread,
            MarketLine.total,
            MarketLine.home_ml,
            MarketLine.away_ml,
            MarketLine.fetched_at,
        )
        .where(
            MarketLine.game_id.in_(list(game_ids)),
            MarketLine.is_closing,
            MarketLine.provider.not_in(AGGREGATORS),
        )
        .order_by(MarketLine.game_id, MarketLine.provider, MarketLine.fetched_at.desc())
        .ext(postgresql.distinct_on(MarketLine.game_id, MarketLine.provider))
    )
    return [LineSnapshot(*row) for row in session.execute(query)]


def _closing_median(session: Session, column, through_season: int) -> dict[int, float]:
    """Same consensus as live grading (book/consensus.py): median of sportsbooks only."""
    query = (
        select(MarketLine.game_id, func.percentile_cont(0.5).within_group(column))
        .join(Game, Game.id == MarketLine.game_id)
        .where(
            MarketLine.is_closing,
            column.is_not(None),
            MarketLine.provider.not_in(AGGREGATORS),
            Game.season <= through_season,
        )
        .group_by(MarketLine.game_id)
    )
    return {game_id: float(value) for game_id, value in session.execute(query)}


def _float(value) -> float | None:
    return None if value is None else float(value)
