"""Simulate the rest of the current regular season from today's forecasts (doc 05 §7).

Every remaining regular-season game gets the published per-game forecast
(services/predict.py, the same model and sigma as the board), and the season Monte
Carlo (sim/season.py) adds rating uncertainty that holds for the whole season. Games
already played count as they ended. Each conference's title game follows from the
simulated standings (sim/conference.py) and counts as a win for its champion. Nothing is
stored here: the nightly `tsi run` saves the result (services/sim_store.py).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
from sqlalchemy.orm import Session

from tsi.db.queries.calendar import calendar_week
from tsi.db.queries.conference import conference_games, conference_members
from tsi.db.queries.schedule import UpcomingGame, upcoming_games
from tsi.db.queries.team_info import Record, records
from tsi.db.queries.teams import team_names
from tsi.divisions import RATED_DIVISION
from tsi.ingest.freshness import current_season
from tsi.model.artifact import ModelArtifact
from tsi.services.conference_setup import build_conferences
from tsi.services.live_inputs import LiveInputs, load_live_inputs
from tsi.services.predict import forecast_game
from tsi.sim.conference import simulate_title, title_odds
from tsi.sim.season import DEFAULT_SIMS, RemainingGame, simulate_games, wins_added
from tsi.sim.uncertainty import LAST_WEEK, game_noise, rating_tau

SEASON_DAYS = 200  # far enough to reach the end of any regular season


@dataclass(frozen=True)
class TeamProjection:
    team_id: int
    conference: str | None
    record: Record  # so far
    remaining: int  # regular-season games left on the schedule (title game not included)
    expected_wins: float  # final wins incl. a simulated conference title game, on average
    win_dist: list[float]  # P(final wins = k) for k = 0, 1, ...
    win_out_prob: float  # P(wins every remaining scheduled game)
    title_game_prob: float | None  # P(plays in its conference title game); None: independent
    conference_title_prob: float | None


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
    left = np.zeros(len(teams), dtype=int)
    for g in remaining:
        left[g.home] += 1
        left[g.away] += 1
    win_out = (added == left).mean(axis=0)  # before any simulated title game

    def neutral(a: int, b: int) -> float:
        game = UpcomingGame(0, season, week, "regular", now, a, b, RATED_DIVISION,
                            RATED_DIVISION, True)  # fmt: skip
        return forecast_game(game, live, artifact).distribution.margin

    members = conference_members(session, season)
    conferences = build_conferences(
        members,
        conference_games(session, season),
        index,
        {g.id: i for i, g in enumerate(upcoming)},
        neutral,
        now,
    )
    odds: dict[int, tuple[float, float]] = {}
    for conf in conferences:
        result = simulate_title(conf, simulated)
        if result.added_game:
            added[np.arange(sims), result.champion] += 1
        odds |= title_odds(result, conf.teams)

    so_far = records(session, season, now)
    conference_of = {m.team_id: m.conference for m in members}
    projections = [
        _projection(
            t,
            conference_of.get(t),
            so_far.get(t, Record()),
            int(left[i]),
            added[:, i],
            float(win_out[i]),
            odds.get(i),
        )
        for i, t in enumerate(fbs)
    ]
    projections.sort(key=lambda p: -p.expected_wins)
    return SeasonProjection(
        season, now, regular_week, tau, sims, projections, team_names(session, fbs)
    )


def _projection(
    team_id: int,
    conference: str | None,
    record: Record,
    left: int,
    added: np.ndarray,
    win_out: float,
    odds: tuple[float, float] | None,
) -> TeamProjection:
    final = record.wins + added
    dist = np.bincount(final, minlength=record.wins + left + 1) / len(final)
    finalist, champion = odds if odds else (None, None)
    return TeamProjection(
        team_id,
        conference,
        record,
        left,
        float(final.mean()),
        dist.tolist(),
        win_out,
        finalist,
        champion,
    )
