"""Team-game offense rows (one per team per completed game) for the ratings fit."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import case, select
from sqlalchemy.orm import Session, aliased

from tsi.db.models import Game, TeamGameStats, TeamSeason


@dataclass(frozen=True)
class OffenseRow:
    """One team's offense in one completed game. Its defense is the opponent's row."""

    game_id: int
    season: int
    start_time: datetime | None
    team_id: int
    opp_id: int
    team_div: str
    opp_div: str
    site: int  # +1 home, -1 away, 0 neutral
    points: int
    drives: int | None
    plays: int | None
    epa_per_play: float | None  # None when CFBD has no advanced stats for the game
    success_rate: float | None


def offense_rows(session: Session, first_season: int, last_season: int) -> list[OffenseRow]:
    """Every team-game with stats in [first_season, last_season], oldest kickoff first."""
    team_ts, opp_ts = aliased(TeamSeason), aliased(TeamSeason)
    opp_id = (Game.home_id + Game.away_id) - TeamGameStats.team_id
    site = case((Game.neutral_site, 0), (TeamGameStats.team_id == Game.home_id, 1), else_=-1)
    query = (
        select(
            Game.id,
            Game.season,
            Game.start_time,
            TeamGameStats.team_id,
            opp_id,
            team_ts.division,
            opp_ts.division,
            site,
            TeamGameStats.points,
            TeamGameStats.drives,
            TeamGameStats.plays,
            TeamGameStats.epa_per_play,
            TeamGameStats.success_rate,
        )
        .join(Game, Game.id == TeamGameStats.game_id)
        .join(team_ts, (team_ts.team_id == TeamGameStats.team_id) & (team_ts.season == Game.season))
        .join(opp_ts, (opp_ts.team_id == opp_id) & (opp_ts.season == Game.season))
        .where(
            Game.completed,
            TeamGameStats.points.is_not(None),
            Game.season.between(first_season, last_season),
        )
        .order_by(Game.start_time, Game.id, TeamGameStats.team_id)
    )
    return [OffenseRow(*row) for row in session.execute(query)]
