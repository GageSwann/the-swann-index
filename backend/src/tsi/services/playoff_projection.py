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
from tsi.divisions import RATED_DIVISION
from tsi.services.compute_rankings import Rankings
from tsi.services.playoff_resume import DivisionResume, simulated_order
from tsi.sim.bracket import MeanMargin, play_bracket
from tsi.sim.cfp import FieldInputs, seeds
from tsi.sim.cfp_format import CfpFormat
from tsi.sim.conference import TitleResults
from tsi.sim.season import SimulatedGames


@dataclass(frozen=True)
class TeamPlayoff:
    make: float  # P(in the field)
    bye: float  # P(a first-round bye: a top-4 CFP seed, a top-8 FCS seed)
    seed_dist: list[float]  # P(seed = s): s = 1..12 (CFP), 1..16 (FCS: the seeded teams)
    quarterfinal: float  # P(reaches the last eight)
    semifinal: float
    final: float
    champion: float


@dataclass(frozen=True)
class PlayoffProjection:
    odds: dict[int, TeamPlayoff]  # team id -> odds
    # (sims, field_size) simulation team index at each seed, per simulated season; None when
    # no field could be formed. Read for the stakes of single games (games of the week).
    field: np.ndarray | None = None


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
) -> PlayoffProjection:
    index = {t: i for i, t in enumerate(inputs.fbs)}
    n = len(inputs.fbs)
    order = simulated_order(
        DivisionResume(inputs.fbs, 0, RATED_DIVISION, rankings.benchmark, rankings.season),
        rankings.ratings,
        sigma,
        inputs.played,
        inputs.remaining,
        inputs.wins,
        inputs.titles.values(),
    )

    champs = [inputs.titles[c].champion for c in fmt.champion_bids if c in inputs.titles]
    group = np.array([inputs.conference_of.get(t) in fmt.group_bid_conferences for t in inputs.fbs])
    field_inputs = FieldInputs(
        np.stack(champs, axis=1),
        group,
        index.get(inputs.independent) if inputs.independent else None,
    )
    seeded = seeds(order, field_inputs, fmt)
    bracket = play_bracket(seeded, sim, mean_margin, fmt)
    odds = {inputs.fbs[i]: _odds(i, bracket, fmt) for i in range(n)}
    return PlayoffProjection(odds, seeded)  # FBS indexes come first in the simulation


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
