"""Stored season simulations (`sim_results`) of a rating run."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import SimResult


@dataclass(frozen=True)
class StoredSim:
    team_id: int
    expected_wins: float
    win_dist: list[float]
    win_out_prob: float
    title_game_prob: float | None
    conference_title_prob: float | None


def stored_sims(session: Session, run_id: int, team_id: int | None = None) -> dict[int, StoredSim]:
    """team id -> its simulation in that run (empty for runs before the sim existed)."""
    query = select(
        SimResult.team_id,
        SimResult.expected_wins,
        SimResult.win_dist,
        SimResult.win_out_prob,
        SimResult.title_game_prob,
        SimResult.conference_title_prob,
    ).where(SimResult.run_id == run_id)
    if team_id is not None:
        query = query.where(SimResult.team_id == team_id)
    return {row[0]: StoredSim(*row) for row in session.execute(query)}
