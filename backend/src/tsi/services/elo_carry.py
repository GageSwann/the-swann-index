"""Build the saved Elo state of finished seasons, and decide whether a live run may use it.

A live run resumes Elo from the committed state (model/elo_carry.py) only when the
database still holds exactly the games it was built from: the database computes a
fingerprint of them (~32 bytes) instead of sending ~3 MB of games (#140, #145).
Anything else (no file, another season, other Elo parameters, a changed game) falls
back to replaying every season, so live results never depend on the shortcut.
"""

import logging

from sqlalchemy.orm import Session

from tsi.db.queries.results import completed_games, completed_games_fingerprint
from tsi.model.elo import EloParams, EloRun, run_elo
from tsi.model.elo_carry import EloCarry, load_carry, rating_params

logger = logging.getLogger(__name__)


def build_elo_carry(session: Session, through_season: int, params: EloParams) -> EloCarry:
    """Replay every completed game with a kickoff through `through_season` (as live runs do)."""
    games = [g for g in completed_games(session, through_season) if g.start_time]
    run = run_elo(games, params)
    return EloCarry(
        through_season=through_season,
        fingerprint=completed_games_fingerprint(session, through_season),
        params=rating_params(params),
        run=EloRun(predictions=[], ratings=run.ratings, divisions=run.divisions, season=run.season),
    )


def starting_elo(
    session: Session, season: int, params: EloParams, carry: EloCarry | None = None
) -> EloRun | None:
    """Elo state at the end of last season if the saved one still holds, else None."""
    carry = carry or load_carry()
    if carry is None or not carry.usable(season, params):
        return None
    if completed_games_fingerprint(session, season - 1) != carry.fingerprint:
        logger.warning(
            "saved Elo state through %s no longer matches the games; replaying all seasons "
            "(rebuild it with `tsi model elo-carry`)",
            carry.through_season,
        )
        return None
    return carry.run
