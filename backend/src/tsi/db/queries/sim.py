"""Stored season simulations (`sim_results`, `sim_game_forecasts`) of a rating run."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import SimGameForecast, SimResult
from tsi.db.queries.filters import one_of


@dataclass(frozen=True)
class StoredSim:
    team_id: int
    expected_wins: float
    win_dist: list[float]
    win_out_prob: float
    title_game_prob: float | None
    conference_title_prob: float | None
    playoff_prob: float | None  # playoff odds: None outside the regular season
    bye_prob: float | None
    seed_dist: list[float] | None
    quarterfinal_prob: float | None
    semifinal_prob: float | None
    final_prob: float | None
    champion_prob: float | None


def stored_sims(session: Session, run_id: int, team_id: int | None = None) -> dict[int, StoredSim]:
    """team id -> its simulation in that run (empty for runs before the sim existed)."""
    query = select(
        SimResult.team_id,
        SimResult.expected_wins,
        SimResult.win_dist,
        SimResult.win_out_prob,
        SimResult.title_game_prob,
        SimResult.conference_title_prob,
        SimResult.playoff_prob,
        SimResult.bye_prob,
        SimResult.seed_dist,
        SimResult.quarterfinal_prob,
        SimResult.semifinal_prob,
        SimResult.final_prob,
        SimResult.champion_prob,
    ).where(SimResult.run_id == run_id)
    if team_id is not None:
        query = query.where(SimResult.team_id == team_id)
    return {row[0]: StoredSim(*row) for row in session.execute(query)}


@dataclass(frozen=True)
class StoredOutlook:
    game_id: int
    proj_home: float
    proj_away: float
    home_win_prob: float
    adjusted: bool


def stored_outlooks(session: Session, run_id: int, game_ids: list[int]) -> dict[int, StoredOutlook]:
    """game id -> the forecast that run's season simulation used (#144); games it didn't
    simulate (played, postseason, runs before #144) are missing."""
    query = select(
        SimGameForecast.game_id,
        SimGameForecast.proj_home,
        SimGameForecast.proj_away,
        SimGameForecast.home_win_prob,
        SimGameForecast.adjusted,
    ).where(SimGameForecast.run_id == run_id, one_of(SimGameForecast.game_id, game_ids))
    return {row[0]: StoredOutlook(*row) for row in session.execute(query)}
