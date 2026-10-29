"""Playoff odds from the simulated seasons (doc 05 §7, decision #100).

In every simulated season: the Résumé ranking from each team's final record (the
committee stand-in, sim/resume_sim.py), the field and seeds under the current format
(sim/cfp.py), then the bracket (sim/bracket.py). Regular season only: once the real
field is set, the projection stops (playing the actual bracket is a later step).
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from tsi.db.queries.results import GameResult
from tsi.db.queries.schedule import UpcomingGame
from tsi.model.ratings.probability import win_prob
from tsi.services.compute_rankings import Rankings
from tsi.sim.bracket import MeanMargin, play_bracket
from tsi.sim.cfp import FieldInputs, seeds
from tsi.sim.cfp_format import CfpFormat
from tsi.sim.conference import TitleResults
from tsi.sim.resume_sim import resume_order, simulated_sor, sor_table
from tsi.sim.season import SimulatedGames


@dataclass(frozen=True)
class TeamPlayoff:
    make: float  # P(in the field)
    bye: float  # P(a top-four seed)
    seed_dist: list[float]  # P(seed = s), s = 1..field size
    quarterfinal: float  # P(reaches the quarterfinals: a bye or a first-round win)
    semifinal: float
    final: float
    champion: float


@dataclass(frozen=True)
class PlayoffInputs:
    fbs: Sequence[int]  # team ids; simulation index = position
    played: Sequence[GameResult]  # this season's finished regular-season games
    remaining: Sequence[UpcomingGame]  # remaining regular-season games
    wins: np.ndarray  # (sims, len(fbs)) final wins, title games included
    titles: dict[str, TitleResults]  # conference -> simulated title results
    conference_of: dict[int, str | None]
    independent: int | None  # team id with the independent bid rule (Notre Dame)


def project_playoff(
    inputs: PlayoffInputs,
    rankings: Rankings,
    sigma: float,
    sim: SimulatedGames,
    mean_margin: MeanMargin,
    fmt: CfpFormat,
) -> dict[int, TeamPlayoff]:
    index = {t: i for i, t in enumerate(inputs.fbs)}
    n = len(inputs.fbs)
    benchmark, hfa = rankings.benchmark, rankings.ratings.hfa

    def p_vs(opp: int, div: str, site: int) -> float:
        return win_prob(benchmark - rankings.ratings.get(opp, div).rating + site * hfa, sigma)

    # Same games as the stored SOR (services/compute_rankings.py): ties don't count.
    games = [g for g in inputs.played if g.margin != 0] + list(inputs.remaining)
    probs: list[list[float]] = [[] for _ in range(n)]
    for g in games:
        for team, opp, opp_div, site in (
            (g.home_id, g.away_id, g.away_div, 0 if g.neutral else 1),
            (g.away_id, g.home_id, g.home_div, 0 if g.neutral else -1),
        ):
            if team in index:
                probs[index[team]].append(p_vs(opp, opp_div, site))
    tables = [sor_table(p) for p in probs]

    season_rating = np.array([rankings.ratings.get(t, "fbs").rating for t in inputs.fbs])
    neutral_p = np.array([win_prob(benchmark - r, sigma) for r in season_rating])
    title_p = np.full(inputs.wins.shape, np.nan)  # benchmark's chance in a title game
    rows = np.arange(inputs.wins.shape[0])
    for result in inputs.titles.values():
        if not result.added_game:
            continue  # a scheduled title game is already in the schedules
        a, b = result.finalists[:, 0], result.finalists[:, 1]
        title_p[rows, a] = neutral_p[b]
        title_p[rows, b] = neutral_p[a]

    sor = simulated_sor(tables, inputs.wins, title_p)
    order = resume_order(sor, inputs.wins, season_rating)

    champs = [inputs.titles[c].champion for c in fmt.champion_bids if c in inputs.titles]
    group = np.array([inputs.conference_of.get(t) in fmt.group_bid_conferences for t in inputs.fbs])
    field_inputs = FieldInputs(
        np.stack(champs, axis=1),
        group,
        index.get(inputs.independent) if inputs.independent else None,
    )
    seeded = seeds(order, field_inputs, fmt)
    bracket = play_bracket(seeded, sim, mean_margin, fmt)
    return {inputs.fbs[i]: _odds(i, bracket, fmt) for i in range(n)}


def _odds(i: int, b, fmt: CfpFormat) -> TeamPlayoff:
    seed_dist = [float((b.seeds[:, s] == i).mean()) for s in range(fmt.field_size)]
    return TeamPlayoff(
        make=float(sum(seed_dist)),
        bye=float(sum(seed_dist[: fmt.byes])),
        seed_dist=seed_dist,
        quarterfinal=float((b.quarterfinalists == i).any(axis=1).mean()),
        semifinal=float((b.semifinalists == i).any(axis=1).mean()),
        final=float((b.finalists == i).any(axis=1).mean()),
        champion=float((b.champion == i).mean()),
    )
