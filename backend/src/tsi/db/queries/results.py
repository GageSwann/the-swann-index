"""Completed games with scores and each side's division, in kickoff order."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
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


def completed_games(
    session: Session, through_season: int, *, from_season: int | None = None
) -> list[GameResult]:
    """Every completed, scored game up to `through_season` (from `from_season` when given,
    else all seasons), oldest kickoff first. Steps that only need one season pass
    `from_season`: the full history is ~3 MB of database reads (#144)."""
    home_ts, away_ts = aliased(TeamSeason), aliased(TeamSeason)
    query = (
        select(
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
        .join(home_ts, (home_ts.team_id == Game.home_id) & (home_ts.season == Game.season))
        .join(away_ts, (away_ts.team_id == Game.away_id) & (away_ts.season == Game.season))
        .where(
            Game.completed,
            Game.home_points.is_not(None),
            Game.away_points.is_not(None),
            Game.season <= through_season,
        )
        .order_by(Game.start_time, Game.id)
    )
    if from_season is not None:
        query = query.where(Game.season >= from_season)
    return [GameResult(*row) for row in session.execute(query)]
