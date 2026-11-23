"""FCS playoff odds from the official bracket (#157), once the real field is set.

The 24 teams and their positions come from `sim/fcs_brackets.py`; CFBD's playoff games
supply what is already decided. Every simulated season plays the rest of the bracket with
the same model, rating shifts and game noise as the regular-season projection
(sim/fcs_playoff.py): finished games keep their winner, scheduled games are played at
their real site, and later rounds at the better seed until the neutral-site final. So
each night's odds follow the real results and predict only the games still to come.
"""

import logging
from collections.abc import Sequence

import numpy as np
from sqlalchemy.orm import Session

from tsi.db.queries.playoff_games import (
    BracketMismatchError,
    PlayoffGame,
    fcs_playoff_schedule,
    official_field,
)
from tsi.services.fcs_playoff_projection import bracket_odds
from tsi.services.playoff_projection import TeamPlayoff
from tsi.sim.bracket import MeanMargin
from tsi.sim.fcs_brackets import FCS_BRACKETS, OfficialBracket
from tsi.sim.fcs_format import FcsFormat
from tsi.sim.fcs_playoff import KnownGames, play_fcs_bracket
from tsi.sim.season import SimulatedGames

logger = logging.getLogger(__name__)


def check_first_round(field: Sequence[int], games: Sequence[PlayoffGame], fmt: FcsFormat) -> None:
    """Every first-round pairing must be one CFBD schedules (hosts may differ)."""
    entered = {frozenset((field[hi - 1], field[lo - 1])) for hi, lo in fmt.first_round}
    scheduled = {frozenset((g.home_id, g.away_id)) for g in games if g.first_round}
    if entered != scheduled:
        raise BracketMismatchError(
            f"first round differs from CFBD: {len(entered - scheduled)} entered pairings "
            f"aren't scheduled, {len(scheduled - entered)} scheduled ones aren't entered"
        )


def known_games(games: Sequence[PlayoffGame], index: dict[int, int]) -> KnownGames:
    """Decided winners and real sites, in simulation indexes."""
    winners: dict[tuple[int, int], int] = {}
    sites: dict[tuple[int, int], tuple[int, bool]] = {}
    for g in games:
        if g.home_id not in index or g.away_id not in index:
            continue
        home, away = index[g.home_id], index[g.away_id]
        pair = (min(home, away), max(home, away))
        sites[pair] = (home, bool(g.neutral))
        if g.winner is not None:
            winners[pair] = index[g.winner]
    return KnownGames(winners, sites)


def official_fcs_odds(
    session: Session,
    season: int,
    fcs: Sequence[int],
    index: dict[int, int],  # team id -> simulation index
    sim: SimulatedGames,
    mean_margin: MeanMargin,  # simulation indexes
    fmt: FcsFormat,
    brackets: dict[int, OfficialBracket] = FCS_BRACKETS,
) -> dict[int, TeamPlayoff] | None:
    """Every FCS team's odds from the official bracket; None when this season has no
    entered bracket or it doesn't match CFBD (logged: the page then shows no FCS odds)."""
    bracket = brackets.get(season)
    if bracket is None:
        return None
    games = fcs_playoff_schedule(session, season)
    try:
        field = official_field(session, bracket.field)
        check_first_round(field, games, fmt)
    except BracketMismatchError:
        logger.exception("FCS bracket %s not used", season)
        return None
    if any(t not in index for t in field):
        logger.error("FCS bracket %s: a team isn't in the simulation", season)
        return None
    sims = sim.shift.shape[0]
    positions = np.tile(np.array([index[t] for t in field]), (sims, 1))
    played = play_fcs_bracket(positions, sim, mean_margin, fmt, known_games(games, index))
    return {t: bracket_odds(index[t], played, fmt) for t in fcs if t in index}
