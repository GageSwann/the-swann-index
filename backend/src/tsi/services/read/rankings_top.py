"""`/rankings/top`: a division's Power and Résumé top N for the home page's rails (#155).

The home page shows only rank, team, record and movement; reading the full rankings (every
team's ratings, both rating sets, sims and records: ~200 KB each, four of them) cost ~0.8
MB of database reads per refresh. This reads the top N's rows only. Ranks, movement and
records follow `/rankings` exactly (same run, same Sunday baseline).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy.orm import Session

from tsi.db.queries.runs import run_and_baseline
from tsi.db.queries.team_info import RankRow, Record, TeamRef, records, season_ranks, team_refs
from tsi.db.queries.team_info import top_ranks as top_rank_rows

TopDivision = Literal["fbs", "fcs"]


@dataclass(frozen=True)
class TopTeam:
    rank: int
    previous_rank: int | None  # same ranking at the Sunday baseline; None: unranked then
    team: TeamRef
    wins: int
    losses: int
    ties: int


@dataclass(frozen=True)
class TopRankings:
    season: int
    week: int
    as_of: datetime
    previous_as_of: datetime | None
    division: TopDivision
    power: list[TopTeam]
    resume: list[TopTeam]


def top_rankings(
    session: Session, season: int, division: TopDivision, n: int = 25
) -> TopRankings | None:
    run, previous = run_and_baseline(session, season, None, None)
    if run is None:
        return None
    rows = top_rank_rows(session, run.id, season, division, n)
    ids = [r.team_id for r in rows]
    before = {r.team_id: r for r in season_ranks(session, previous.id, ids)} if previous else {}
    teams = team_refs(session, season, ids)
    record = records(session, season, run.run_at, ids)

    def side(key: str) -> list[TopTeam]:
        ranked = sorted(
            (r for r in rows if (getattr(r, key) or n + 1) <= n), key=lambda r: getattr(r, key)
        )
        return [_team(r, key, before.get(r.team_id), teams[r.team_id], record) for r in ranked]

    return TopRankings(
        season=run.season,
        week=run.week,
        as_of=run.run_at,
        previous_as_of=previous.run_at if previous else None,
        division=division,
        power=side("rank_power"),
        resume=side("rank_resume"),
    )


def _team(
    r: RankRow, key: str, before: RankRow | None, team: TeamRef, record: dict[int, Record]
) -> TopTeam:
    rec = record.get(r.team_id, Record())
    return TopTeam(
        rank=getattr(r, key),
        previous_rank=getattr(before, key) if before else None,
        team=team,
        wins=rec.wins,
        losses=rec.losses,
        ties=rec.ties,
    )
