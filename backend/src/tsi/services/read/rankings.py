"""`/rankings`: Power or Résumé rankings from a stored daily rating run."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy.orm import Session

from tsi.db.queries.runs import run_and_baseline, run_params
from tsi.db.queries.sim import StoredSim, stored_sims
from tsi.db.queries.team_info import (
    Record,
    StoredRating,
    TeamRef,
    records,
    stored_ratings,
    team_refs,
)
from tsi.divisions import FCS, RATED_DIVISION
from tsi.services.read.resume_view import benchmark_ranks

RankingType = Literal["power", "resume"]
Division = Literal["fbs", "fcs", "all"]  # "all": FBS and FCS on one scale (Power only)


class MixedResumeError(ValueError):
    """Résumé ranks compare against a division's own benchmark, so they can't be mixed."""


@dataclass(frozen=True)
class RankedTeam:
    rank: int  # in the requested ranking
    previous_rank: int | None  # same ranking at the baseline (`previous_as_of`); None: unranked
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
    sor: float | None  # strength of record: chance the benchmark (#12 FBS / #24 FCS) matches it
    sos: float | None  # strength of schedule: mean current rating of opponents played
    off_rank: int  # offense rating among ranked FBS teams (1 = best)
    def_rank: int  # defense rating (positive = better defense)
    predictive_rating: float | None  # the prediction model's rating (prior + Elo blended in)
    predictive_rank: int | None
    projected_wins: float | None  # season sim (decision #98); None for runs before it
    conference_title_prob: float | None  # None: independents, or no sim


@dataclass(frozen=True)
class Rankings:
    season: int
    season_type: str
    week: int
    as_of: datetime
    previous_as_of: datetime | None  # the baseline: last run of the latest Sunday before (#126)
    model_version: str
    type: RankingType
    teams: list[RankedTeam]
    division: Division
    # The Résumé benchmark this run used for the division: #12 FBS, #24 FCS (#10 before
    # 2026-11-06, #133). None for "all", which has no Résumé.
    benchmark_rank: int | None = None


def rankings(
    session: Session,
    season: int,
    ranking: RankingType = "power",
    week: int | None = None,
    season_type: str | None = None,
    division: Division = RATED_DIVISION,
) -> Rankings | None:
    """Ranks are within a division (decision #111); "all" re-ranks both by rating."""
    if division == "all" and ranking == "resume":
        raise MixedResumeError("Résumé rankings are per division; pick fbs or fcs.")
    run, previous = run_and_baseline(session, season, week, season_type)
    if run is None:
        return None
    stored = stored_ratings(session, [run.id] + ([previous.id] if previous else []))
    rows = stored.get(run.id, [])
    season_rows = [r for r in rows if r.basis == "season"]
    predictive = {r.team_id: r for r in rows if r.basis == "predictive"}
    teams = team_refs(session, season, [r.team_id for r in season_rows])
    listed = (RATED_DIVISION, FCS) if division == "all" else (division,)
    season_rows = [r for r in season_rows if teams[r.team_id].division in listed]
    record = records(session, season, run.run_at)
    sims = stored_sims(session, run.id)
    key = "rank_power" if ranking == "power" else "rank_resume"
    rank = _ranks(season_rows, key, division)
    ranked = sorted((r for r in season_rows if r.team_id in rank), key=lambda r: rank[r.team_id])
    previous_rows = [
        r
        for r in (stored.get(previous.id, []) if previous else [])
        if r.basis == "season" and r.team_id in teams and teams[r.team_id].division in listed
    ]
    # Movement only when the earlier run ranked every listed division (the first FCS
    # rankings would otherwise all read "new", and "all" would mix in phantom moves).
    ranked_before = {teams[r.team_id].division for r in previous_rows if getattr(r, key)}
    if not set(listed) <= ranked_before:
        previous, previous_rows = None, []
    before = _ranks(previous_rows, key, division)
    off_rank = _rank_by(ranked, lambda r: r.off_rating)
    def_rank = _rank_by(ranked, lambda r: r.def_rating)
    bench_rank = None
    if division != "all":
        fbs_rank, fcs_rank = benchmark_ranks(run_params(session, run.id))
        bench_rank = fcs_rank if division == FCS else fbs_rank
    return Rankings(
        season=run.season,
        season_type=run.season_type,
        week=run.week,
        as_of=run.run_at,
        previous_as_of=previous.run_at if previous else None,
        model_version=run.model_version,
        type=ranking,
        teams=[
            _ranked(
                r,
                rank[r.team_id],
                before.get(r.team_id),
                (off_rank[r.team_id], def_rank[r.team_id]),
                teams[r.team_id],
                record.get(r.team_id, Record()),
                predictive,
                sims.get(r.team_id),
            )
            for r in ranked
        ],
        division=division,
        benchmark_rank=bench_rank,
    )


def _ranks(rows: list[StoredRating], key: str, division: Division) -> dict[int, int]:
    """team -> rank: the stored (within-division) rank, or for "all" by rating."""
    ranked = [r for r in rows if getattr(r, key) is not None]
    if division != "all":
        return {r.team_id: getattr(r, key) for r in ranked}
    return {r.team_id: i + 1 for i, r in enumerate(sorted(ranked, key=lambda r: -r.rating))}


def _rank_by(rows: list[StoredRating], value) -> dict[int, int]:
    """team -> 1-based rank by `value` (higher is better)."""
    ordered = sorted(rows, key=value, reverse=True)
    return {r.team_id: i + 1 for i, r in enumerate(ordered)}


def _ranked(
    r: StoredRating,
    rank: int,
    previous_rank: int | None,
    side_ranks: tuple[int, int],
    team: TeamRef,
    rec: Record,
    predictive: dict[int, StoredRating],
    sim: StoredSim | None,
) -> RankedTeam:
    p = predictive.get(r.team_id)
    return RankedTeam(
        rank=rank,
        previous_rank=previous_rank,
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
        sos=r.sos,
        off_rank=side_ranks[0],
        def_rank=side_ranks[1],
        predictive_rating=p.rating if p else None,
        predictive_rank=p.rank_power if p else None,
        projected_wins=sim.expected_wins if sim else None,
        conference_title_prob=sim.conference_title_prob if sim else None,
    )
