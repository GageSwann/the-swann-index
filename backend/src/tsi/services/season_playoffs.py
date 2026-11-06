"""Playoff odds for both divisions from one simulated season set (services/season_sim.py).

FBS teams: the College Football Playoff (services/playoff_projection.py, #100). FCS
teams: the 24-team FCS bracket (services/fcs_playoff_projection.py, #125). Simulation
indexes: FBS teams first, then FCS teams, in the order of `SeasonState.fbs` / `.fcs`.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
from sqlalchemy.orm import Session

from tsi.db.queries.conference import moved_up_teams
from tsi.db.queries.results import GameResult
from tsi.db.queries.schedule import UpcomingGame
from tsi.db.queries.team_info import team_ids_by_slug
from tsi.services.compute_rankings import Rankings
from tsi.services.fcs_playoff_projection import FcsPlayoffInputs, project_fcs_playoff
from tsi.services.playoff_projection import PlayoffInputs, PlayoffProjection, project_playoff
from tsi.sim.cfp_format import CfpFormat
from tsi.sim.conference import TitleResults
from tsi.sim.fcs_format import FcsFormat
from tsi.sim.season import SimulatedGames


@dataclass(frozen=True)
class SeasonState:
    season: int
    fbs: Sequence[int]
    fcs: Sequence[int]
    played: Sequence[GameResult]  # this season's finished games
    remaining: Sequence[UpcomingGame]  # remaining regular-season games
    wins: np.ndarray  # (sims, len(fbs) + len(fcs)) final wins, title games included
    titles: dict[str, TitleResults]  # conference -> simulated champion
    conference_of: dict[int, str | None]
    sim: SimulatedGames
    margin: Callable[[int, int, bool], float]  # simulation indexes -> a's mean margin


def fbs_playoff(
    session: Session, state: SeasonState, rankings: Rankings, sigma: float, fmt: CfpFormat
) -> PlayoffProjection:
    slug, _ = fmt.independent_bid or ("", 0)
    return project_playoff(
        PlayoffInputs(
            fbs=state.fbs,
            played=state.played,
            remaining=state.remaining,
            wins=state.wins[:, : len(state.fbs)],
            titles=state.titles,
            conference_of=state.conference_of,
            independent=team_ids_by_slug(session, [slug]).get(slug),
        ),
        rankings,
        sigma,
        state.sim,
        state.margin,
        fmt,
    )


def fcs_playoff(
    session: Session, state: SeasonState, rankings: Rankings, sigma: float, fmt: FcsFormat
) -> PlayoffProjection:
    if not state.fcs or rankings.fcs_benchmark is None:
        return PlayoffProjection({})
    moving_up = team_ids_by_slug(session, list(fmt.moving_up))
    return project_fcs_playoff(
        FcsPlayoffInputs(
            fcs=state.fcs,
            offset=len(state.fbs),
            played=state.played,
            remaining=state.remaining,
            wins=state.wins[:, len(state.fbs) :],
            titles=state.titles,
            conference_of=state.conference_of,
            ineligible=moved_up_teams(session, state.season, fmt.reclass_seasons)
            | set(moving_up.values()),
        ),
        rankings.ratings,
        rankings.fcs_benchmark,
        state.season,
        sigma,
        state.sim,
        state.margin,
        fmt,
    )
