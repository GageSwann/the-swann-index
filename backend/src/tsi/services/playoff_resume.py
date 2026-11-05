"""The Résumé order at the end of every simulated season, for one division's teams.

Shared by the CFP (services/playoff_projection.py) and FCS (services/fcs_playoff_projection.py)
projectors: the committee stand-in (#100, #125). SOR uses the same games as the stored
ranking (ties don't count) plus the remaining schedule, against the division's
benchmark (#12 FBS, #24 FCS); opponents keep today's ratings. A simulated conference
title game adds one game against that simulation's opponent.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

from tsi.db.queries.results import GameResult
from tsi.db.queries.schedule import UpcomingGame
from tsi.model.ratings.probability import win_prob
from tsi.model.ratings.types import RatingSet
from tsi.sim.conference import TitleResults
from tsi.sim.resume_sim import resume_order, simulated_sor, sor_table


@dataclass(frozen=True)
class DivisionResume:
    teams: Sequence[int]  # team ids; local index = position
    offset: int  # simulation index of teams[0] (the division's block in the sim's team list)
    division: str
    benchmark: float  # the division's Résumé benchmark rating
    season: int


def simulated_order(
    d: DivisionResume,
    ratings: RatingSet,
    sigma: float,
    played: Sequence[GameResult],
    remaining: Sequence[UpcomingGame],
    wins: np.ndarray,  # (sims, len(teams)) final wins, title games included
    titles: Iterable[TitleResults],
) -> np.ndarray:
    """(sims, len(teams)) local team indexes, best Résumé first."""
    index = {t: i for i, t in enumerate(d.teams)}
    n = len(d.teams)

    def p_vs(opp: int, div: str, site: int) -> float:
        rating = ratings.get(opp, div, d.season).rating
        return win_prob(d.benchmark - rating + site * ratings.hfa, sigma)

    games = [g for g in played if g.margin != 0] + list(remaining)
    probs: list[list[float]] = [[] for _ in range(n)]
    for g in games:
        for team, opp, opp_div, site in (
            (g.home_id, g.away_id, g.away_div, 0 if g.neutral else 1),
            (g.away_id, g.home_id, g.home_div, 0 if g.neutral else -1),
        ):
            if team in index:
                probs[index[team]].append(p_vs(opp, opp_div, site))
    tables = [sor_table(p) for p in probs]

    rating = np.array([ratings.get(t, d.division, d.season).rating for t in d.teams])
    neutral_p = np.array([win_prob(d.benchmark - r, sigma) for r in rating])
    title_p = np.full(wins.shape, np.nan)  # benchmark's chance in a title game
    rows = np.arange(wins.shape[0])
    for result in titles:
        if not result.added_game or result.finalists is None:
            continue  # a scheduled title game is already in the schedules
        a, b = result.finalists[:, 0] - d.offset, result.finalists[:, 1] - d.offset
        if not (a.min() >= 0 and a.max() < n and b.min() >= 0 and b.max() < n):
            continue  # another division's conference
        title_p[rows, a] = neutral_p[b]
        title_p[rows, b] = neutral_p[a]

    sor = simulated_sor(tables, wins, title_p)
    return resume_order(sor, wins, rating)
