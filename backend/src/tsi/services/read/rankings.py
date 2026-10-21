"""`/rankings`: Power or Résumé rankings from a stored daily rating run."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy.orm import Session

from tsi.db.queries.runs import latest_rating_run
from tsi.db.queries.team_info import (
    Record,
    StoredRating,
    TeamRef,
    records,
    stored_ratings,
    team_refs,
)

RankingType = Literal["power", "resume"]


@dataclass(frozen=True)
class RankedTeam:
    rank: int  # in the requested ranking
    team: TeamRef
    wins: int
    losses: int
    ties: int
    rating: float  # `season` rating: points vs. an average FBS team, this season only
    off_rating: float
    def_rating: float
    games_played: int
    provisional: bool  # fewer than 4 games
    rank_power: int | None
    rank_resume: int | None
    sor: float | None  # strength of record: chance a #12 team matches this record
    predictive_rating: float | None  # the prediction model's rating (prior + Elo blended in)
    predictive_rank: int | None


@dataclass(frozen=True)
class Rankings:
    season: int
    season_type: str
    week: int
    as_of: datetime
    model_version: str
    type: RankingType
    teams: list[RankedTeam]


def rankings(
    session: Session,
    season: int,
    ranking: RankingType = "power",
    week: int | None = None,
    season_type: str | None = None,
) -> Rankings | None:
    run = latest_rating_run(session, season, week, season_type)
    if run is None:
        return None
    rows = stored_ratings(session, [run.id]).get(run.id, [])
    season_rows = [r for r in rows if r.basis == "season"]
    predictive = {r.team_id: r for r in rows if r.basis == "predictive"}
    teams = team_refs(session, season, [r.team_id for r in season_rows])
    record = records(session, season, run.run_at)
    key = "rank_power" if ranking == "power" else "rank_resume"
    ranked = sorted(
        (r for r in season_rows if getattr(r, key) is not None), key=lambda r: getattr(r, key)
    )
    return Rankings(
        season=run.season,
        season_type=run.season_type,
        week=run.week,
        as_of=run.run_at,
        model_version=run.model_version,
        type=ranking,
        teams=[
            _ranked(
                r, getattr(r, key), teams[r.team_id], record.get(r.team_id, Record()), predictive
            )
            for r in ranked
        ],
    )


def _ranked(
    r: StoredRating, rank: int, team: TeamRef, rec: Record, predictive: dict[int, StoredRating]
) -> RankedTeam:
    p = predictive.get(r.team_id)
    return RankedTeam(
        rank=rank,
        team=team,
        wins=rec.wins,
        losses=rec.losses,
        ties=rec.ties,
        rating=r.rating,
        off_rating=r.off_rating,
        def_rating=r.def_rating,
        games_played=r.games_played,
        provisional=r.provisional,
        rank_power=r.rank_power,
        rank_resume=r.rank_resume,
        sor=r.sor,
        predictive_rating=p.rating if p else None,
        predictive_rank=p.rank_power if p else None,
    )
