"""Games that have not kicked off yet (what gets predicted and published)."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, aliased

from tsi.db.models import Game, TeamSeason

RATED_DIVISION = "fbs"


@dataclass(frozen=True)
class UpcomingGame:
    id: int
    season: int
    week: int
    season_type: str
    start_time: datetime
    home_id: int
    away_id: int
    home_div: str
    away_div: str
    neutral: bool


def upcoming_games(session: Session, after: datetime, until: datetime) -> list[UpcomingGame]:
    """Games kicking off in (after, until] with at least one rated (FBS) team, by kickoff."""
    home_ts, away_ts = aliased(TeamSeason), aliased(TeamSeason)
    query = (
        select(
            Game.id,
            Game.season,
            Game.week,
            Game.season_type,
            Game.start_time,
            Game.home_id,
            Game.away_id,
            home_ts.division,
            away_ts.division,
            Game.neutral_site,
        )
        .join(home_ts, (home_ts.team_id == Game.home_id) & (home_ts.season == Game.season))
        .join(away_ts, (away_ts.team_id == Game.away_id) & (away_ts.season == Game.season))
        .where(
            Game.start_time > after,
            Game.start_time <= until,
            or_(home_ts.division == RATED_DIVISION, away_ts.division == RATED_DIVISION),
        )
        .order_by(Game.start_time, Game.id)
    )
    return [UpcomingGame(*row) for row in session.execute(query)]
