"""Games that have not kicked off yet (what gets predicted and published)."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, literal, or_, select
from sqlalchemy.orm import Session, aliased

from tsi.db.models import Game, TeamSeason
from tsi.divisions import FCS, FCS_STATS_FROM, RATED_DIVISION


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


def upcoming_games(
    session: Session, after: datetime, until: datetime, *, with_fcs: bool = False
) -> list[UpcomingGame]:
    """Games kicking off in (after, until] with at least one FBS team, by kickoff.

    `with_fcs` adds FCS-vs-FCS games from FCS_STATS_FROM (both teams rated, #109).
    """
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
            or_(
                home_ts.division == RATED_DIVISION,
                away_ts.division == RATED_DIVISION,
                and_(
                    literal(with_fcs),
                    home_ts.division == FCS,
                    away_ts.division == FCS,
                    Game.season >= FCS_STATS_FROM,
                ),
            ),
        )
        .order_by(Game.start_time, Game.id)
    )
    return [UpcomingGame(*row) for row in session.execute(query)]
