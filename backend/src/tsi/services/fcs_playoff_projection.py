"""FCS playoff odds from the simulated seasons (Phase 11, decision #125).

In every simulated season: the FCS Résumé order from each team's final record (the
committee stand-in, services/playoff_resume.py; it picked 88 of the 96 real fields'
teams in 2022-25), the automatic bids (each auto-bid conference's best-placed eligible
team), at-large bids by that order, 16 seeds, and the 24-team bracket (sim/fcs_playoff.py).
Regular season only, and only until the real field is set.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from tsi.db.queries.results import GameResult
from tsi.db.queries.schedule import UpcomingGame
from tsi.divisions import FCS
from tsi.model.ratings.types import RatingSet
from tsi.services.playoff_projection import TeamPlayoff
from tsi.services.playoff_resume import DivisionResume, simulated_order
from tsi.sim.bracket import MeanMargin
from tsi.sim.conference import TitleResults
from tsi.sim.fcs_format import FcsFormat
from tsi.sim.fcs_playoff import FcsBracket, fcs_field, play_fcs_bracket
from tsi.sim.season import SimulatedGames


@dataclass(frozen=True)
class FcsPlayoffInputs:
    fcs: Sequence[int]  # team ids; simulation index = offset + position
    offset: int
    played: Sequence[GameResult]  # this season's finished regular-season games
    remaining: Sequence[UpcomingGame]  # remaining regular-season games
    wins: np.ndarray  # (sims, len(fcs)) final wins
    titles: dict[str, TitleResults]  # conference -> simulated champion / standings
    conference_of: dict[int, str | None]
    ineligible: set[int]  # team ids that can't be picked (moving up or down a level)


def project_fcs_playoff(
    inputs: FcsPlayoffInputs,
    ratings: RatingSet,
    benchmark: float,  # the #10 FCS team's rating
    season: int,
    sigma: float,
    sim: SimulatedGames,
    mean_margin: MeanMargin,  # simulation indexes
    fmt: FcsFormat,
) -> dict[int, TeamPlayoff]:
    n = len(inputs.fcs)
    order = simulated_order(
        DivisionResume(inputs.fcs, inputs.offset, FCS, benchmark, season),
        ratings,
        sigma,
        inputs.played,
        inputs.remaining,
        inputs.wins,
        [inputs.titles[c] for c in inputs.titles],
    )
    eligible = np.array(
        [
            t not in inputs.ineligible and inputs.conference_of.get(t) not in fmt.no_playoff
            for t in inputs.fcs
        ]
    )
    bids = np.stack(
        [
            _bid(inputs.titles[c], eligible, inputs.offset, n)
            for c in fmt.champion_bids
            if c in inputs.titles
        ]
        or [np.full(order.shape[0], -1)],
        axis=1,
    )
    field = fcs_field(order, bids, eligible, fmt)
    if field is None:
        return {}
    bracket = play_fcs_bracket(field + inputs.offset, sim, mean_margin, fmt)
    return {t: _odds(inputs.offset + i, bracket, fmt) for i, t in enumerate(inputs.fcs)}


def _bid(result: TitleResults, eligible: np.ndarray, offset: int, n: int) -> np.ndarray:
    """(sims,) local index of the conference's bid holder: its champion, or the best-placed
    eligible team when the champion can't go; -1 if nobody can."""
    standings = (
        result.standings
        if result.standings is not None
        else result.champion[:, None]  # a title-game conference: its champion only
    ) - offset
    ok = eligible[np.clip(standings, 0, n - 1)] & (standings >= 0) & (standings < n)
    first = ok.argmax(axis=1)
    rows = np.arange(len(first))
    return np.where(ok[rows, first], standings[rows, first], -1)


def _odds(i: int, b: FcsBracket, fmt: FcsFormat) -> TeamPlayoff:
    seed_dist = [float((b.field[:, s] == i).mean()) for s in range(fmt.seeds)]
    return TeamPlayoff(
        make=float((b.field == i).any(axis=1).mean()),
        bye=float(sum(seed_dist[: fmt.byes])),
        seed_dist=seed_dist,
        quarterfinal=float((b.quarterfinalists == i).any(axis=1).mean()),
        semifinal=float((b.semifinalists == i).any(axis=1).mean()),
        final=float((b.finalists == i).any(axis=1).mean()),
        champion=float((b.champion == i).mean()),
    )
