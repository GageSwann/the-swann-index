"""Completed games with scores and each side's division, in kickoff order."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Select, String, cast, func, literal_column, select
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.orm import Session, aliased

from tsi.db.models import Game, TeamSeason
from tsi.divisions import RATED_DIVISION


@dataclass(frozen=True)
class GameResult:
    id: int
    season: int
    start_time: datetime | None
    home_id: int
    away_id: int
    home_div: str
    away_div: str
    neutral: bool
    home_points: int
    away_points: int

    @property
    def margin(self) -> int:
        return self.home_points - self.away_points

    @property
    def fbs_vs_fbs(self) -> bool:
        return self.home_div == RATED_DIVISION and self.away_div == RATED_DIVISION


def _sides() -> tuple[Any, Any]:
    return aliased(TeamSeason), aliased(TeamSeason)


def _filtered(
    query: Select[Any], home_ts: Any, away_ts: Any, through_season: int, from_season: int | None
) -> Select[Any]:
    query = (
        query.join(home_ts, (home_ts.team_id == Game.home_id) & (home_ts.season == Game.season))
        .join(away_ts, (away_ts.team_id == Game.away_id) & (away_ts.season == Game.season))
        .where(
            Game.completed,
            Game.home_points.is_not(None),
            Game.away_points.is_not(None),
            Game.season <= through_season,
        )
    )
    if from_season is not None:
        query = query.where(Game.season >= from_season)
    return query


def completed_games(
    session: Session, through_season: int, *, from_season: int | None = None
) -> list[GameResult]:
    """Every completed, scored game up to `through_season` (from `from_season` when given,
    else all seasons), oldest kickoff first. Steps that only need one season pass
    `from_season`: the full history is ~3 MB of database reads (#144)."""
    home_ts, away_ts = _sides()
    query = select(
        Game.id,
        Game.season,
        Game.start_time,
        Game.home_id,
        Game.away_id,
        home_ts.division,
        away_ts.division,
        Game.neutral_site,
        Game.home_points,
        Game.away_points,
    )
    query = _filtered(query, home_ts, away_ts, through_season, from_season)
    return [GameResult(*row) for row in session.execute(query.order_by(Game.start_time, Game.id))]


def completed_games_fingerprint(session: Session, through_season: int) -> str:
    """md5 of the completed games with a kickoff up to `through_season`, in replay order,
    computed by the database: a few bytes of transfer instead of the games themselves.
    Equal fingerprints mean the same games, results, divisions and order
    (model/elo_carry.py)."""
    home_ts, away_ts = _sides()
    fields = (
        Game.id,
        Game.season,
        func.extract("epoch", Game.start_time),  # independent of the server's time zone
        Game.home_id,
        Game.away_id,
        home_ts.division,
        away_ts.division,
        Game.neutral_site,
        Game.home_points,
        Game.away_points,
    )
    row = func.concat_ws(",", *(cast(f, String) for f in fields))
    # string_agg(row, ';' ORDER BY ...): the ORDER BY goes after the separator.
    separator = aggregate_order_by(literal_column("';'"), Game.start_time, Game.id)
    digest = func.md5(func.string_agg(row, separator))
    query = _filtered(select(digest).select_from(Game), home_ts, away_ts, through_season, None)
    return session.execute(query.where(Game.start_time.is_not(None))).scalar_one() or ""
