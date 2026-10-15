"""Résumé ranking: strength of record vs. a typical #12 team (doc 04 §7, decision #24).

SOR = P(a benchmark team, playing this exact schedule, wins at least as many games).
Lower SOR = harder to match = more impressive. Win probabilities come from the
opponents' CURRENT `season` ratings, so past wins are re-valued every day as
opponents rise or fall (dynamic strength of schedule). Retrospective by design,
so this is not look-ahead (rule 1 applies to predictions).
"""

from collections.abc import Sequence
from dataclasses import dataclass

from tsi.model.ratings.probability import win_prob

BENCHMARK_RANK = 12
# Log-loss fit of `season` margins on 2015-22 games where both teams had 4+ games.
SEASON_SIGMA = 15.7


@dataclass(frozen=True)
class ScheduleGame:
    opponent_rating: float  # opponent's CURRENT season rating
    site: int  # +1 this team at home, -1 away, 0 neutral
    won: bool


@dataclass(frozen=True)
class Resume:
    wins: int
    losses: int
    sor: float  # P(benchmark wins >= wins); lower is better
    benchmark_expected_wins: float  # how many the benchmark would expect to win
    sos: float  # mean opponent rating (points vs. average FBS team)


def poisson_binomial(probs: Sequence[float]) -> list[float]:
    """dist[k] = P(exactly k successes) for independent trials with these probabilities."""
    dist = [1.0]
    for p in probs:
        dist = [
            (dist[k] if k < len(dist) else 0.0) * (1 - p) + (dist[k - 1] * p if k > 0 else 0.0)
            for k in range(len(dist) + 1)
        ]
    return dist


def benchmark_rating(ratings: Sequence[float], rank: int = BENCHMARK_RANK) -> float:
    ordered = sorted(ratings, reverse=True)
    return ordered[min(rank, len(ordered)) - 1] if ordered else 0.0


def strength_of_record(
    games: Sequence[ScheduleGame], benchmark: float, hfa: float, sigma: float = SEASON_SIGMA
) -> Resume:
    wins = sum(g.won for g in games)
    probs = [win_prob(benchmark - g.opponent_rating + g.site * hfa, sigma) for g in games]
    dist = poisson_binomial(probs)
    sos = sum(g.opponent_rating for g in games) / len(games) if games else 0.0
    return Resume(
        wins=wins,
        losses=len(games) - wins,
        sor=sum(dist[wins:]),
        benchmark_expected_wins=sum(probs),
        sos=sos,
    )
