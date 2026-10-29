"""Simulate the rest of the current regular season from today's forecasts (doc 05 §7).

Every remaining regular-season game gets the published per-game forecast
(services/predict.py, the same model and sigma as the board), and the season Monte
Carlo (sim/season.py) adds rating uncertainty that holds for the whole season. Games
already played count as they ended. Each conference's title game follows from the
simulated standings (sim/conference.py) and counts as a win for its champion; playoff
odds follow from each simulated season's final records (services/playoff_projection.py,
regular season only). Nothing is stored here: the nightly `tsi run` saves the result
(services/sim_store.py).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
from sqlalchemy.orm import Session

from tsi.db.queries.calendar import calendar_week
from tsi.db.queries.conference import conference_games, conference_members
from tsi.db.queries.results import completed_games
from tsi.db.queries.schedule import UpcomingGame, upcoming_games
from tsi.db.queries.team_info import Record, records, team_ids_by_slug
from tsi.db.queries.teams import team_names
from tsi.divisions import RATED_DIVISION
from tsi.ingest.freshness import current_season
from tsi.model.artifact import ModelArtifact
from tsi.services.compute_rankings import Rankings, build_rankings
from tsi.services.conference_setup import build_conferences
from tsi.services.live_inputs import LiveInputs, load_live_inputs
from tsi.services.playoff_projection import PlayoffInputs, TeamPlayoff, project_playoff
from tsi.services.predict import forecast_game
from tsi.sim.cfp_format import FORMAT_2026, CfpFormat
from tsi.sim.conference import TitleResults, simulate_title, title_odds
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
    playoff: TeamPlayoff | None = None  # None once the regular season is over


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
    rankings: Rankings | None = None,  # today's, if already computed (the nightly run)
    fmt: CfpFormat = FORMAT_2026,
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

    def margin(a: int, b: int, neutral: bool = True) -> float:
        """Team a's mean margin vs. FBS team b (a at home unless neutral)."""
        game = UpcomingGame(0, season, week, "regular", now, a, b, RATED_DIVISION,
                            RATED_DIVISION, neutral)  # fmt: skip
        return forecast_game(game, live, artifact).distribution.margin

    members = conference_members(session, season)
    conferences = build_conferences(
        members,
        conference_games(session, season),
        index,
        {g.id: i for i, g in enumerate(upcoming)},
        margin,
        now,
    )
    odds: dict[int, tuple[float, float]] = {}
    titles: dict[str, TitleResults] = {}
    for conf in conferences:
        result = titles[conf.name] = simulate_title(conf, simulated)
        if result.added_game:
            added[np.arange(sims), result.champion] += 1
        odds |= title_odds(result, conf.teams)

    so_far = records(session, season, now)
    conference_of = {m.team_id: m.conference for m in members}
    playoff: dict[int, TeamPlayoff] = {}
    if season_type == "regular":
        slug, _ = fmt.independent_bid or ("", 0)
        playoff = project_playoff(
            PlayoffInputs(
                fbs=fbs,
                played=[
                    g
                    for g in completed_games(session, season)
                    if g.season == season and g.start_time and g.start_time < now
                ],  # fmt: skip
                remaining=upcoming,
                wins=np.array([so_far.get(t, Record()).wins for t in fbs]) + added[:, : len(fbs)],
                titles=titles,
                conference_of=conference_of,
                independent=team_ids_by_slug(session, [slug]).get(slug),
            ),
            rankings
            or build_rankings(session, season, now, artifact.rating, artifact.sigma_season),
            artifact.sigma_season,
            simulated,
            lambda a, b, neutral: margin(fbs[a], fbs[b], neutral),
            fmt,
        )
    projections = [
        _projection(
            t,
            conference_of.get(t),
            so_far.get(t, Record()),
            int(left[i]),
            added[:, i],
            float(win_out[i]),
            odds.get(i),
            playoff.get(t),
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
    playoff: TeamPlayoff | None = None,
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
        playoff,
    )
