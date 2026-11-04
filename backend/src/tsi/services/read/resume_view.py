"""The Résumé breakdown on a team page: each game's difficulty for the benchmark team.

The benchmark is a typical #12 FBS team, or a typical #10 FCS team for FCS teams (owner,
#91; decision #114). Mirrors the nightly ranking (`services/rate.py` ->
`compute_rankings.py`) exactly (decision #89): opponents' ratings are their CURRENT
`season` ratings from the shown rating run (their own stored rating whenever they have
one, else the pooled rating), home field is that run's `season_hfa`, the win-probability
spread is the production model's `sigma_season`, and only decided games kicked off before
the run count. Recomputing SOR from these games reproduces the stored value.
"""

from dataclasses import dataclass, replace
from datetime import datetime
from functools import lru_cache
from typing import Any

from sqlalchemy.orm import Session

from tsi.db.queries.games import GameRow
from tsi.db.queries.runs import RunInfo, run_params
from tsi.db.queries.team_info import StoredRating, TeamRef, stored_ratings
from tsi.divisions import FCS, RATED_DIVISION
from tsi.model.artifact import load_artifact
from tsi.model.ratings.probability import win_prob
from tsi.model.resume import ScheduleGame, benchmark_rating, strength_of_record


@dataclass(frozen=True)
class ResumeSummary:
    benchmark_rating: float  # the benchmark team's `season` rating (#12 FBS / #10 FCS)
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
    fcs_benchmark: float | None = None  # #10 FCS team (#91), in runs from 2026-11-04

    def for_division(self, division: str) -> "ResumeContext | None":
        """The context for a team of `division`; None when that run has no benchmark for it."""
        if division == RATED_DIVISION:
            return self
        if division == FCS and self.fcs_benchmark is not None:
            return replace(self, benchmark=self.fcs_benchmark, division=FCS)
        return None


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
        fcs_benchmark=params.get("fcs_resume_benchmark"),  # saved from 2026-11-04 (#111)
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
    row = ctx.season.get(opponent.id)  # FBS, and FCS from 2022 (#109): its own rating
    if row is not None:
        # Ranks are within a division, so only an opponent from the team's own shows one.
        return row.rating, row.rank_power if opponent.division == ctx.division else None
    if opponent.division == RATED_DIVISION:
        return 0.0, None  # an FBS team without games is rated average, as in the fit
    if ctx.pooled is None:
        return None, None
    return ctx.pooled["fcs" if opponent.division == "fcs" else "lower"], None


@lru_cache(maxsize=1)
def _artifact_sigma() -> float:
    return load_artifact().sigma_season
