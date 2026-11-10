"""The Résumé breakdown on a team page: each game's difficulty for the benchmark team.

The benchmark is a typical #12 FBS team, or a typical #24 FCS team for FCS teams (#133;
#10 in runs before 2026-11-06, #91, #114). Mirrors the nightly ranking (`services/rate.py` ->
`compute_rankings.py`) exactly (decision #89): opponents' ratings are their CURRENT
`season` ratings from the shown rating run (their own stored rating whenever they have
one, else the pooled rating), home field is that run's `season_hfa`, the win-probability
spread is the production model's `sigma_season`, and only decided games kicked off before
the run count. Recomputing SOR from these games reproduces the stored value.
"""

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from tsi.db.queries.games import GameRow
from tsi.db.queries.runs import RunInfo, run_params
from tsi.db.queries.team_info import StoredRating, TeamRef, stored_ratings
from tsi.divisions import FCS, RATED_DIVISION
from tsi.model.artifact import production_artifact
from tsi.model.ratings.probability import win_prob
from tsi.model.resume import (
    BENCHMARK_RANK,
    LEGACY_FCS_BENCHMARK_RANK,
    ScheduleGame,
    benchmark_rating,
    strength_of_record,
)


@dataclass(frozen=True)
class ResumeSummary:
    benchmark_rating: float  # the benchmark team's `season` rating
    benchmark_rank: int  # which team that is: #12 FBS / #24 FCS (#10 FCS before 2026-11-06)
    games: int  # decided games that count (kicked off before the run)
    sor: float | None  # stored SOR: P(the benchmark wins at least as many); lower = better
    # What the benchmark team would expect from those games; None while any counted game's
    # difficulty is unknown (runs saved before pooled non-FBS ratings were, #89).
    benchmark_expected_wins: float | None


@dataclass(frozen=True)
class GameDifficulty:
    opponent_rating: float | None  # current `season` rating (pooled if it has none)
    opponent_rank: int | None  # current Power rank, only when in the team's own division
    benchmark_win_prob: float | None  # P(the benchmark team wins this game)
    in_resume: bool  # decided and kicked off before the shown run


@dataclass(frozen=True)
class ResumeContext:
    run_at: datetime
    benchmark: float  # of `division`
    hfa: float | None
    sigma: float  # win-probability spread used for SOR
    season: dict[int, StoredRating]  # team id -> `season` rating in the run
    pooled: dict[str, float] | None  # "fcs" / "lower" -> pooled rating
    division: str = RATED_DIVISION  # whose Résumé: sets the benchmark and shown ranks
    fcs_benchmark: float | None = None  # FCS benchmark rating, in runs from 2026-11-04
    benchmark_rank: int = BENCHMARK_RANK  # of `division`
    fcs_benchmark_rank: int = LEGACY_FCS_BENCHMARK_RANK

    def for_division(self, division: str) -> "ResumeContext | None":
        """The context for a team of `division`; None when that run has no benchmark for it."""
        if division == RATED_DIVISION:
            return self
        if division == FCS and self.fcs_benchmark is not None:
            return replace(
                self,
                benchmark=self.fcs_benchmark,
                benchmark_rank=self.fcs_benchmark_rank,
                division=FCS,
            )
        return None


def resume_context(session: Session, run: RunInfo) -> ResumeContext:
    """Two round trips: every team's ratings in the run, and the run's parameters."""
    rows = stored_ratings(session, [run.id], basis="season").get(run.id, [])
    params: dict[str, Any] = run_params(session, run.id)
    season = {r.team_id: r for r in rows}
    benchmark = params.get("resume_benchmark")
    if benchmark is None:
        benchmark = benchmark_rating([r.rating for r in rows])
    fbs_rank, fcs_rank = benchmark_ranks(params)
    return ResumeContext(
        run_at=run.run_at,
        benchmark=float(benchmark),
        hfa=params.get("season_hfa"),
        # Saved with each run from 2026-10-28; older runs used the production artifact's.
        sigma=float(params.get("resume_sigma") or production_artifact().sigma_season),
        season=season,
        pooled=params.get("pooled_season_ratings"),  # saved from 2026-10-28 (#89)
        fcs_benchmark=params.get("fcs_resume_benchmark"),  # saved from 2026-11-04 (#111)
        benchmark_rank=fbs_rank,
        fcs_benchmark_rank=fcs_rank,
    )


def benchmark_ranks(params: dict[str, Any]) -> tuple[int, int]:
    """(FBS, FCS) Résumé benchmark ranks a run used; saved with each run from 2026-11-06
    (#133). Older runs: #12 FBS, #10 FCS."""
    return (
        int(params.get("resume_benchmark_rank", BENCHMARK_RANK)),
        int(params.get("fcs_resume_benchmark_rank", LEGACY_FCS_BENCHMARK_RANK)),
    )


def game_difficulty(
    ctx: ResumeContext, g: GameRow, team_id: int, opponent: TeamRef
) -> GameDifficulty:
    rating, rank = _opponent_rating(ctx, opponent)
    prob = (
        None
        if rating is None or ctx.hfa is None
        else win_prob(ctx.benchmark - rating + _site(g, team_id) * ctx.hfa, ctx.sigma)
    )
    decided = (
        g.completed
        and g.home_points is not None
        and g.away_points is not None
        and g.home_points != g.away_points
    )
    in_resume = bool(decided and g.start_time and g.start_time < ctx.run_at)
    return GameDifficulty(rating, rank, prob, in_resume)


def resume_summary(
    ctx: ResumeContext, games: list[GameRow], team_id: int, refs: dict[int, TeamRef]
) -> ResumeSummary:
    """Every rated team gets one: rank and SOR are the stored ranking's (canonical); the
    expected wins need every counted game's difficulty and are None otherwise."""
    probs = [
        d.benchmark_win_prob
        for g in games
        if (d := game_difficulty(ctx, g, team_id, _opponent(g, team_id, refs))).in_resume
    ]
    row = ctx.season.get(team_id)
    return ResumeSummary(
        benchmark_rating=ctx.benchmark,
        benchmark_rank=ctx.benchmark_rank,
        games=len(probs),
        sor=row.sor if row else None,
        # The expected wins are the sum of each counted game's chance; unknown if any is.
        benchmark_expected_wins=None if None in probs else sum(p for p in probs if p is not None),
    )


def recomputed_sor(
    ctx: ResumeContext, games: list[GameRow], team_id: int, refs: dict[int, TeamRef]
) -> float | None:
    """SOR rebuilt from the breakdown (tests check it equals the stored value); None if any
    counted game's difficulty is unknown."""
    counted: list[ScheduleGame] = []
    for g in games:
        d = game_difficulty(ctx, g, team_id, _opponent(g, team_id, refs))
        if not d.in_resume:
            continue
        if d.opponent_rating is None or ctx.hfa is None:
            return None
        won = (g.home_points > g.away_points) == (g.home_id == team_id)  # type: ignore[operator]
        counted.append(ScheduleGame(d.opponent_rating, _site(g, team_id), won))
    if ctx.hfa is None:
        return None
    return strength_of_record(counted, ctx.benchmark, ctx.hfa, ctx.sigma).sor


def _site(g: GameRow, team_id: int) -> int:
    """+1 at home, -1 away, 0 neutral, from the team's side."""
    return 0 if g.neutral else (1 if g.home_id == team_id else -1)


def _opponent(g: GameRow, team_id: int, refs: dict[int, TeamRef]) -> TeamRef:
    return refs[g.away_id if g.home_id == team_id else g.home_id]


def _opponent_rating(ctx: ResumeContext, opponent: TeamRef) -> tuple[float | None, int | None]:
    row = ctx.season.get(opponent.id)  # FBS, and FCS from 2022 (#109): its own rating
    if row is not None:
        # Ranks are within a division, so only an opponent from the team's own shows one.
        return row.rating, row.rank_power if opponent.division == ctx.division else None
    if opponent.division == RATED_DIVISION:
        return 0.0, None  # an FBS team without games is rated average, as in the fit
    if ctx.pooled is None:
        return None, None
    return ctx.pooled["fcs" if opponent.division == "fcs" else "lower"], None
