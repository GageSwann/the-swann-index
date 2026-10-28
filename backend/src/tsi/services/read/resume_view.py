"""The Résumé breakdown on a team page: each game's difficulty for a typical #12 team.

Mirrors the nightly ranking (`services/rate.py` -> `compute_rankings.py`) exactly
(decision #89): opponents' ratings are their CURRENT `season` ratings from the shown
rating run (FBS teams individually, non-FBS teams pooled), home field is that run's
`season_hfa`, the win-probability spread is the production model's `sigma_season`, and
only decided games kicked off before the run count. Recomputing SOR from these games
reproduces the stored value.
"""

from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Any

from sqlalchemy.orm import Session

from tsi.db.queries.games import GameRow
from tsi.db.queries.runs import RunInfo, run_params
from tsi.db.queries.team_info import StoredRating, TeamRef, stored_ratings
from tsi.divisions import RATED_DIVISION
from tsi.model.artifact import load_artifact
from tsi.model.ratings.probability import win_prob
from tsi.model.resume import ScheduleGame, benchmark_rating, strength_of_record


@dataclass(frozen=True)
class ResumeSummary:
    benchmark_rating: float  # the #12 team's `season` rating in the shown run
    games: int  # decided games that count (kicked off before the run)
    sor: float | None  # stored Résumé SOR: P(a #12 team wins at least as many); lower = better
    # What a #12 team would expect from those games; None while any counted game's
    # difficulty is unknown (runs saved before pooled non-FBS ratings were, #89).
    benchmark_expected_wins: float | None


@dataclass(frozen=True)
class GameDifficulty:
    opponent_rating: float | None  # current `season` rating (pooled for non-FBS)
    opponent_rank: int | None  # current Power rank (FBS only)
    benchmark_win_prob: float | None  # P(a typical #12 team wins this game)
    in_resume: bool  # decided and kicked off before the shown run


@dataclass(frozen=True)
class ResumeContext:
    run_at: datetime
    benchmark: float
    hfa: float | None
    sigma: float  # win-probability spread used for SOR
    season: dict[int, StoredRating]  # team id -> `season` rating in the run
    pooled: dict[str, float] | None  # "fcs" / "lower" -> pooled rating


def resume_context(session: Session, run: RunInfo) -> ResumeContext:
    """Two round trips: every team's ratings in the run, and the run's parameters."""
    rows = [r for r in stored_ratings(session, [run.id]).get(run.id, []) if r.basis == "season"]
    params: dict[str, Any] = run_params(session, run.id)
    season = {r.team_id: r for r in rows}
    benchmark = params.get("resume_benchmark")
    if benchmark is None:
        benchmark = benchmark_rating([r.rating for r in rows])
    return ResumeContext(
        run_at=run.run_at,
        benchmark=float(benchmark),
        hfa=params.get("season_hfa"),
        # Saved with each run from 2026-10-28; older runs used the production artifact's.
        sigma=float(params.get("resume_sigma") or _artifact_sigma()),
        season=season,
        pooled=params.get("pooled_season_ratings"),  # saved from 2026-10-28 (#89)
    )


def game_difficulty(
    ctx: ResumeContext, g: GameRow, team_id: int, opponent: TeamRef
) -> GameDifficulty:
    home = g.home_id == team_id
    site = 0 if g.neutral else (1 if home else -1)
    rating, rank = _opponent_rating(ctx, opponent)
    prob = (
        None
        if rating is None or ctx.hfa is None
        else win_prob(ctx.benchmark - rating + site * ctx.hfa, ctx.sigma)
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
        home = g.home_id == team_id
        d = game_difficulty(ctx, g, team_id, _opponent(g, team_id, refs))
        if not d.in_resume:
            continue
        if d.opponent_rating is None or ctx.hfa is None:
            return None
        won = (g.home_points > g.away_points) == home  # type: ignore[operator]
        site = 0 if g.neutral else (1 if home else -1)
        counted.append(ScheduleGame(d.opponent_rating, site, won))
    if ctx.hfa is None:
        return None
    return strength_of_record(counted, ctx.benchmark, ctx.hfa, ctx.sigma).sor


def _opponent(g: GameRow, team_id: int, refs: dict[int, TeamRef]) -> TeamRef:
    return refs[g.away_id if g.home_id == team_id else g.home_id]


def _opponent_rating(ctx: ResumeContext, opponent: TeamRef) -> tuple[float | None, int | None]:
    if opponent.division == RATED_DIVISION:
        row = ctx.season.get(opponent.id)
        # An FBS team without games is rated average, as in the fit.
        return (row.rating, row.rank_power) if row else (0.0, None)
    if ctx.pooled is None:
        return None, None
    return ctx.pooled["fcs" if opponent.division == "fcs" else "lower"], None


@lru_cache(maxsize=1)
def _artifact_sigma() -> float:
    return load_artifact().sigma_season
