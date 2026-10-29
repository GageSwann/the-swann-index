"""Simulate the rest of the current regular season from today's forecasts (doc 05 §7).

Every remaining regular-season game gets the published per-game forecast
(services/predict.py, the same model and sigma as the board), and the season Monte
Carlo (sim/season.py) adds rating uncertainty that holds for the whole season. Games
already played count as they ended. Read-only: nothing is stored.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
from sqlalchemy.orm import Session

from tsi.db.queries.calendar import calendar_week
from tsi.db.queries.schedule import upcoming_games
from tsi.db.queries.team_info import Record, records
from tsi.db.queries.teams import team_names
from tsi.ingest.freshness import current_season
from tsi.model.artifact import ModelArtifact
from tsi.services.live_inputs import LiveInputs, load_live_inputs
from tsi.services.predict import forecast_game
from tsi.sim.season import DEFAULT_SIMS, RemainingGame, simulate_games, wins_added
from tsi.sim.uncertainty import LAST_WEEK, game_noise, rating_tau

SEASON_DAYS = 200  # far enough to reach the end of any regular season


@dataclass(frozen=True)
class TeamProjection:
    team_id: int
    record: Record  # so far
    remaining: int  # regular-season games left on the schedule
    expected_wins: float  # final regular-season wins, on average
    win_dist: list[float]  # P(final wins = k) for k = 0, 1, ...


@dataclass(frozen=True)
class SeasonProjection:
    season: int
    as_of: datetime
    week: int  # regular-season week the uncertainty is set for
    tau: float
    sims: int
    teams: list[TeamProjection]  # FBS teams, most expected wins first
    names: dict[int, str]  # team id -> school, for display


def project_season(
    session: Session,
    now: datetime,
    artifact: ModelArtifact,
    sims: int = DEFAULT_SIMS,
    live: LiveInputs | None = None,
) -> SeasonProjection:
    season = current_season(now)
    live = live or load_live_inputs(session, season, now, artifact)
    upcoming = [
        g
        for g in upcoming_games(session, now, now + timedelta(days=SEASON_DAYS))
        if g.season == season and g.season_type == "regular"
    ]
    season_type, week = calendar_week(session, season, now)
    regular_week = week if season_type == "regular" else LAST_WEEK
    tau = rating_tau(regular_week)

    fbs = sorted(live.fbs)
    teams = fbs + sorted({t for g in upcoming for t in (g.home_id, g.away_id)} - live.fbs)
    index = {t: i for i, t in enumerate(teams)}
    remaining = [
        RemainingGame(
            index[g.home_id],
            index[g.away_id],
            forecast_game(g, live, artifact).distribution.margin,
        )
        for g in upcoming
    ]
    noise = game_noise(artifact.distribution.sigma_margin, tau)
    simulated = simulate_games(remaining, len(teams), tau, noise, sims)
    added = wins_added(simulated, remaining, len(teams))

    so_far = records(session, season, now)
    left = np.zeros(len(teams), dtype=int)
    for g in remaining:
        left[g.home] += 1
        left[g.away] += 1
    projections = [
        _projection(t, so_far.get(t, Record()), int(left[i]), added[:, i])
        for i, t in enumerate(fbs)
    ]
    projections.sort(key=lambda p: -p.expected_wins)
    return SeasonProjection(
        season, now, regular_week, tau, sims, projections, team_names(session, fbs)
    )


def _projection(team_id: int, record: Record, left: int, added: np.ndarray) -> TeamProjection:
    final = record.wins + added
    dist = np.bincount(final, minlength=record.wins + left + 1) / len(final)
    return TeamProjection(team_id, record, left, float(final.mean()), dist.tolist())
