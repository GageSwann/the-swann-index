"""Simulate the rest of the current regular season from today's forecasts (doc 05 §7).

Every remaining regular-season game gets the published per-game forecast
(services/predict.py, the same model and sigma as the board), and the season Monte
Carlo (sim/season.py) adds rating uncertainty that holds for the whole season. Games
already played count as they ended. Each conference's champion follows from the
simulated standings (sim/conference.py): FBS title games count as a win for their
champion; most FCS conferences have none (#125). Playoff odds follow from each
simulated season's final records (services/season_playoffs.py: the CFP for FBS teams,
the 24-team FCS bracket for FCS teams; regular season only). FBS and FCS teams share
one simulation, so their games against each other agree. Nothing is stored here: the
nightly `tsi run` saves the result (services/sim_store.py).
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np
from sqlalchemy.orm import Session

from tsi.db.queries.calendar import calendar_week
from tsi.db.queries.conference import conference_games, conference_members, fcs_playoff_games
from tsi.db.queries.results import completed_games
from tsi.db.queries.schedule import UpcomingGame, upcoming_games
from tsi.db.queries.team_info import Record, records
from tsi.db.queries.teams import team_names
from tsi.divisions import FCS, RATED_DIVISION
from tsi.ingest.freshness import current_season
from tsi.model.artifact import ModelArtifact
from tsi.services.compute_rankings import Rankings, build_rankings
from tsi.services.conference_setup import build_conferences
from tsi.services.live_inputs import LiveInputs, load_live_inputs
from tsi.services.playoff_projection import TeamPlayoff
from tsi.services.predict import forecast_game
from tsi.services.season_playoffs import SeasonState, fbs_playoff, fcs_playoff
from tsi.sim.cfp_format import FORMAT_2026, CfpFormat
from tsi.sim.conference import TitleResults, simulate_title, title_odds
from tsi.sim.fcs_format import FCS_FORMAT_2026, FcsFormat
from tsi.sim.season import DEFAULT_SIMS, RemainingGame, SimulatedGames, simulate_games, wins_added
from tsi.sim.stakes import GameStakes, team_stakes
from tsi.sim.uncertainty import LAST_WEEK, game_noise, rating_tau

logger = logging.getLogger(__name__)
SEASON_DAYS = 200  # far enough to reach the end of any regular season
STAKES_DAYS = 8  # games whose stakes are measured: the coming week's (games of the week)


@dataclass(frozen=True)
class TeamProjection:
    team_id: int
    conference: str | None
    record: Record  # so far
    remaining: int  # regular-season games left on the schedule (title game not included)
    expected_wins: float  # final wins incl. a simulated conference title game, on average
    win_dist: list[float]  # P(final wins = k) for k = 0, 1, ...
    win_out_prob: float  # P(wins every remaining scheduled game)
    title_game_prob: float | None  # P(plays in its conference title game); None: no such game
    conference_title_prob: float | None
    playoff: TeamPlayoff | None = None  # None once the regular season (or its field) is set
    division: str = RATED_DIVISION  # fbs / fcs


@dataclass(frozen=True)
class SeasonProjection:
    season: int
    as_of: datetime
    week: int  # regular-season week the uncertainty is set for
    tau: float
    sims: int
    teams: list[TeamProjection]  # FBS, then FCS teams; most expected wins first in each
    names: dict[int, str]  # team id -> school, for display
    # game id -> what a win is worth to each side, for games in the next STAKES_DAYS
    # between two rated teams (#141); empty outside the regular season.
    game_stakes: dict[int, GameStakes] = field(default_factory=dict)


def project_season(
    session: Session,
    now: datetime,
    artifact: ModelArtifact,
    sims: int = DEFAULT_SIMS,
    live: LiveInputs | None = None,
    rankings: Rankings | None = None,  # today's, if already computed (the nightly run)
    fmt: CfpFormat = FORMAT_2026,
    fcs_fmt: FcsFormat = FCS_FORMAT_2026,
) -> SeasonProjection:
    season = current_season(now)
    live = live or load_live_inputs(session, season, now, artifact)
    fcs_field_set = fcs_playoff_games(session, season)  # empty until the FCS field is picked
    upcoming = [
        g
        for g in upcoming_games(session, now, now + timedelta(days=SEASON_DAYS), with_fcs=True)
        if g.season == season and g.season_type == "regular" and g.id not in fcs_field_set
    ]
    season_type, week = calendar_week(session, season, now)
    regular_week = week if season_type == "regular" else LAST_WEEK
    tau = rating_tau(regular_week)

    fbs, fcs = sorted(live.fbs), sorted(live.fcs)
    rated = [*fbs, *fcs]
    teams = rated + sorted({t for g in upcoming for t in (g.home_id, g.away_id)} - set(rated))
    index = {t: i for i, t in enumerate(teams)}
    division_of = {t: RATED_DIVISION for t in fbs} | {t: FCS for t in fcs}
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
        """Team a's mean margin vs. team b (both rated; a at home unless neutral)."""
        game = UpcomingGame(0, season, week, "regular", now, a, b, division_of[a],
                            division_of[b], neutral)  # fmt: skip
        return forecast_game(game, live, artifact, scheduled=False).distribution.margin

    members = conference_members(session, season, (RATED_DIVISION, FCS))
    conferences = build_conferences(
        members,
        conference_games(session, season),
        index,
        {g.id: i for i, g in enumerate(upcoming)},
        margin,
        now,
        fcs_fmt.title_game_conferences,
    )
    odds: dict[int, tuple[float | None, float]] = {}
    titles: dict[str, TitleResults] = {}
    for conf in conferences:
        result = titles[conf.name] = simulate_title(conf, simulated)
        if result.added_game:
            added[np.arange(sims), result.champion] += 1
        odds |= title_odds(result, conf.teams)

    so_far = records(session, season, now)
    playoff: dict[int, TeamPlayoff] = {}
    stakes: dict[int, GameStakes] = {}
    if season_type == "regular":
        state = SeasonState(
            season=season,
            fbs=fbs,
            fcs=fcs,
            played=[
                g
                for g in completed_games(session, season)
                if g.season == season and g.start_time and g.start_time < now
            ],  # fmt: skip
            remaining=upcoming,
            wins=np.array([so_far.get(t, Record()).wins for t in rated]) + added[:, : len(rated)],
            titles=titles,
            conference_of={m.team_id: m.conference for m in members},
            sim=simulated,
            margin=lambda a, b, neutral: margin(teams[a], teams[b], neutral),
        )
        rankings = rankings or build_rankings(
            session, season, now, artifact.rating, artifact.sigma_season
        )
        fbs_proj = fbs_playoff(session, state, rankings, artifact.sigma_season, fmt)
        playoff = dict(fbs_proj.odds)
        fcs_field = None
        if not fcs_field_set:
            fcs_proj = fcs_playoff(session, state, rankings, artifact.sigma_season, fcs_fmt)
            playoff |= fcs_proj.odds
            fcs_field = fcs_proj.field
        conference_index = {index[m.team_id]: m.conference for m in members if m.team_id in index}
        stakes = _safe_stakes(
            upcoming,
            simulated,
            index,
            len(fbs),
            len(rated),
            (fbs_proj.field, fcs_field),
            {i: titles[c].champion for i, c in conference_index.items() if c in titles},
            now + timedelta(days=STAKES_DAYS),
        )

    conference_of = {m.team_id: m.conference for m in members}
    projections = {
        t: _projection(
            t,
            conference_of.get(t),
            so_far.get(t, Record()),
            int(left[i]),
            added[:, i],
            float(win_out[i]),
            odds.get(i),
            playoff.get(t),
            division_of[t],
        )
        for i, t in enumerate(rated)
    }
    ordered = [
        projections[t]
        for group in (fbs, fcs)
        for t in sorted(group, key=lambda t: -projections[t].expected_wins)
    ]
    return SeasonProjection(
        season, now, regular_week, tau, sims, ordered, team_names(session, rated), stakes
    )


def _safe_stakes(*args) -> dict[int, GameStakes]:
    """Stakes are an extra for the games of the week: a failure here must not lose the
    night's simulation, so it's logged and the picks go without stakes."""
    try:
        return _game_stakes(*args)
    except Exception:
        logger.exception("game stakes failed; games of the week go without them")
        return {}


def _game_stakes(
    upcoming: list[UpcomingGame],  # in simulation column order
    simulated: SimulatedGames,
    index: dict[int, int],  # team id -> simulation index
    n_fbs: int,
    n_rated: int,
    fields: tuple[np.ndarray | None, np.ndarray | None],  # FBS, FCS playoff fields
    champion: dict[int, np.ndarray],  # simulation index -> its conference's champion
    until: datetime,
) -> dict[int, GameStakes]:
    """Stakes of each game before `until` between two rated teams (#141)."""
    out: dict[int, GameStakes] = {}
    for j, g in enumerate(upcoming):
        home, away = index[g.home_id], index[g.away_id]
        if g.start_time is None or g.start_time >= until or max(home, away) >= n_rated:
            continue
        home_won = simulated.home_wins[:, j]

        def side(i: int, won: np.ndarray):
            return team_stakes(i, won, fields[0] if i < n_fbs else fields[1], champion.get(i))

        out[g.id] = GameStakes(side(home, home_won), side(away, ~home_won))
    return out


def _projection(
    team_id: int,
    conference: str | None,
    record: Record,
    left: int,
    added: np.ndarray,
    win_out: float,
    odds: tuple[float | None, float] | None,
    playoff: TeamPlayoff | None = None,
    division: str = RATED_DIVISION,
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
        division,
    )
