"""Team-game offense rows (one per team per completed game) for the ratings fit."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Select, String, case, cast, func, literal_column, select
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.orm import Session, aliased

from tsi.db.models import Game, TeamGameStats, TeamSeason

ORDER = (Game.start_time, Game.id, TeamGameStats.team_id)  # oldest kickoff first
NULL_MARK = "~"  # stands in for NULL in a fingerprint (concat_ws would drop the field)


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
    second_level_yards: float | None = None  # rushing yards 5-10 past the line, per rush (#122)
    power_success: float | None = None  # short-yardage conversion rate (#122)


def offense_rows(session: Session, first_season: int, last_season: int) -> list[OffenseRow]:
    """Every team-game with stats in [first_season, last_season], oldest kickoff first."""
    columns, finish = _offense(first_season, last_season)
    query = finish(select(*columns)).order_by(*ORDER)
    return [OffenseRow(*row) for row in session.execute(query)]


def offense_rows_fingerprint(session: Session, season: int) -> str:
    """md5 of exactly what `offense_rows(session, season, season)` returns, every column in
    its order, computed by the database: ~32 bytes of transfer instead of the rows. Equal
    fingerprints mean the same rows (model/component_carry.py). Floats print as their
    shortest exact text (Postgres 12+), kickoffs as epochs (independent of time zone)."""
    columns, finish = _offense(season, season)
    as_text = [
        func.coalesce(
            cast(func.extract("epoch", c) if c is Game.start_time else c, String), NULL_MARK
        )
        for c in columns
    ]
    row = func.concat_ws(",", *as_text)
    # string_agg(row, ';' ORDER BY ...): the ORDER BY goes after the separator.
    digest = func.md5(func.string_agg(row, aggregate_order_by(literal_column("';'"), *ORDER)))
    return session.execute(finish(select(digest))).scalar_one() or ""


def _offense(first_season: int, last_season: int) -> tuple[list[Any], Any]:
    """The row columns, and a function adding the joins and filters to a select of them."""
    team_ts, opp_ts = aliased(TeamSeason), aliased(TeamSeason)
    opp_id = (Game.home_id + Game.away_id) - TeamGameStats.team_id
    site = case((Game.neutral_site, 0), (TeamGameStats.team_id == Game.home_id, 1), else_=-1)
    columns = [
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
        TeamGameStats.second_level_yards,
        TeamGameStats.power_success,
    ]

    def finish(query: Select[Any]) -> Select[Any]:
        return (
            query.select_from(TeamGameStats)
            .join(Game, Game.id == TeamGameStats.game_id)
            .join(
                team_ts,
                (team_ts.team_id == TeamGameStats.team_id) & (team_ts.season == Game.season),
            )
            .join(opp_ts, (opp_ts.team_id == opp_id) & (opp_ts.season == Game.season))
            .where(
                Game.completed,
                TeamGameStats.points.is_not(None),
                Game.season.between(first_season, last_season),
            )
        )

    return columns, finish
