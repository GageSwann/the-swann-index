"""Compute Power and Résumé rankings for one season as of a moment, per division.

(Stored rankings are read for the API by `services/read/rankings.py`.)

Power  = `season` rating (this season's games only; decision #23/#38).
Résumé = strength of record vs. a typical #12 team (FBS) or #24 team (FCS, #133), with
opponents' current ratings. Ranks are within each division; FCS teams are ranked from
FCS_STATS_FROM, when they are rated individually (decision #109).
Teams with fewer than 4 games are marked provisional.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import Team
from tsi.db.queries.priors import division_teams, fbs_teams
from tsi.db.queries.results import GameResult, completed_games
from tsi.db.queries.stats import offense_rows
from tsi.divisions import FCS, FCS_STATS_FROM
from tsi.model.config import ESTABLISHED_GAMES
from tsi.model.ratings.fit import RatingParams, RatingSet, fit_ratings
from tsi.model.resume import (
    BENCHMARK_RANK,
    FCS_BENCHMARK_RANK,
    SEASON_SIGMA,
    Resume,
    ScheduleGame,
    benchmark_rating,
    strength_of_record,
)
from tsi.services.live_inputs import LiveInputs


@dataclass(frozen=True)
class TeamRanking:
    team_id: int
    rating: float
    off: float
    defense: float
    games: int
    provisional: bool
    rank_power: int
    resume: Resume
    rank_resume: int


@dataclass(frozen=True)
class Rankings:
    season: int
    as_of: datetime
    ratings: RatingSet
    benchmark: float  # FBS Résumé benchmark (#12 FBS team's rating)
    teams: list[TeamRanking]  # FBS, in Power order
    names: dict[int, str]
    fcs_benchmark: float | None = None  # #24 FCS team's rating (#133)
    fcs_teams: list[TeamRanking] = field(default_factory=list)  # FCS, in Power order

    @property
    def fcs_average(self) -> float | None:
        if not self.fcs_teams:
            return None
        return sum(t.rating for t in self.fcs_teams) / len(self.fcs_teams)


def build_rankings(
    session: Session,
    season: int,
    as_of: datetime,
    params: RatingParams | None = None,
    sigma: float = SEASON_SIGMA,
    live: LiveInputs | None = None,  # the run's inputs: their season rows and games are reused
) -> Rankings:
    params = params or RatingParams()
    shared = live is not None and live.shares(season, as_of)
    rows = (
        list(live.season_rows)
        if shared
        else [
            r
            for r in offense_rows(session, season, season)
            if r.start_time and r.start_time < as_of
        ]
    )
    ratings = fit_ratings(rows, params)
    fbs = fbs_teams(session, season, season).get(season, set())
    fcs = (
        division_teams(session, season, season, FCS).get(season, set())
        if season >= FCS_STATS_FROM
        else set()
    )
    games = live.season_games if shared else completed_games(session, season, from_season=season)
    schedules = _schedules(games, season, as_of, ratings, {*fbs, *fcs})
    teams, benchmark = rank_division(fbs, ratings, schedules, BENCHMARK_RANK, sigma)
    fcs_teams, fcs_benchmark = rank_division(fcs, ratings, schedules, FCS_BENCHMARK_RANK, sigma)
    names = {tid: school for tid, school in session.execute(select(Team.id, Team.school))}
    return Rankings(
        season,
        as_of,
        ratings,
        benchmark,
        teams,
        names,
        fcs_benchmark if fcs_teams else None,
        fcs_teams,
    )


def _schedules(
    games: Iterable[GameResult], season: int, as_of: datetime, ratings: RatingSet, teams: set[int]
) -> dict[int, list[ScheduleGame]]:
    """Each team's decided games so far, with opponents' current ratings (ties don't count)."""
    schedules: dict[int, list[ScheduleGame]] = {t: [] for t in teams}
    for g in games:
        if g.season != season or not g.start_time or g.start_time >= as_of or g.margin == 0:
            continue
        for team, opp, opp_div, site, won in (
            (g.home_id, g.away_id, g.away_div, 0 if g.neutral else 1, g.margin > 0),
            (g.away_id, g.home_id, g.home_div, 0 if g.neutral else -1, g.margin < 0),
        ):
            if team in schedules:
                opp_rating = ratings.get(opp, opp_div, season).rating
                schedules[team].append(ScheduleGame(opp_rating, site, won))
    return schedules


def rank_division(
    division: set[int],
    ratings: RatingSet,
    schedules: dict[int, list[ScheduleGame]],
    benchmark_rank: int,
    sigma: float,
) -> tuple[list[TeamRanking], float]:
    """Power and Résumé ranks within one division (teams without a rating are left out)."""
    rated = {t: ratings.teams[t] for t in division if t in ratings.teams}
    benchmark = benchmark_rating([r.rating for r in rated.values()], benchmark_rank)
    resumes = {t: strength_of_record(schedules[t], benchmark, ratings.hfa, sigma) for t in rated}
    power_order = sorted(rated, key=lambda t: -rated[t].rating)
    resume_order = sorted(rated, key=lambda t: (resumes[t].sor, -resumes[t].wins, -rated[t].rating))
    resume_rank = {t: i + 1 for i, t in enumerate(resume_order)}
    teams = [
        TeamRanking(
            team_id=t,
            rating=rated[t].rating,
            off=rated[t].off,
            defense=rated[t].defense,
            games=ratings.games.get(t, 0),
            provisional=ratings.games.get(t, 0) < ESTABLISHED_GAMES,
            rank_power=i + 1,
            resume=resumes[t],
            rank_resume=resume_rank[t],
        )
        for i, t in enumerate(power_order)
    ]
    return teams, benchmark
