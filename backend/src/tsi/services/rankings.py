"""Power and Résumé rankings for one season as of a moment in time (FBS teams).

Power  = `season` rating (this season's games only; decision #23/#38).
Résumé = strength of record vs. a typical #12 team, with opponents' current ratings.
Teams with fewer than 4 games are marked provisional.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.backtest.walk_forward import ESTABLISHED_GAMES
from tsi.db.models import Team
from tsi.db.queries.priors import fbs_teams
from tsi.db.queries.results import completed_games
from tsi.db.queries.stats import offense_rows
from tsi.model.ratings.design import rated_id
from tsi.model.ratings.fit import RatingParams, RatingSet, fit_ratings
from tsi.model.resume import Resume, ScheduleGame, benchmark_rating, strength_of_record


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
    benchmark: float
    teams: list[TeamRanking]  # in Power order
    names: dict[int, str]


def build_rankings(
    session: Session, season: int, as_of: datetime, params: RatingParams | None = None
) -> Rankings:
    params = params or RatingParams()
    rows = [
        r for r in offense_rows(session, season, season) if r.start_time and r.start_time < as_of
    ]
    ratings = fit_ratings(rows, params)
    fbs = fbs_teams(session, season, season).get(season, set())
    rated = {t: ratings.teams[t] for t in fbs if t in ratings.teams}
    benchmark = benchmark_rating([r.rating for r in rated.values()])

    schedules: dict[int, list[ScheduleGame]] = {t: [] for t in rated}
    for g in completed_games(session, season):
        if g.season != season or not g.start_time or g.start_time >= as_of or g.margin == 0:
            continue
        for team, opp, opp_div, site, won in (
            (g.home_id, g.away_id, g.away_div, 0 if g.neutral else 1, g.margin > 0),
            (g.away_id, g.home_id, g.home_div, 0 if g.neutral else -1, g.margin < 0),
        ):
            if team in schedules:
                opp_rating = ratings.get(opp, opp_div).rating
                schedules[team].append(ScheduleGame(opp_rating, site, won))

    resumes = {t: strength_of_record(schedules[t], benchmark, ratings.hfa) for t in rated}
    power_order = sorted(rated, key=lambda t: -rated[t].rating)
    resume_order = sorted(rated, key=lambda t: (resumes[t].sor, -resumes[t].wins, -rated[t].rating))
    resume_rank = {t: i + 1 for i, t in enumerate(resume_order)}
    teams = [
        TeamRanking(
            team_id=t,
            rating=rated[t].rating,
            off=rated[t].off,
            defense=rated[t].defense,
            games=ratings.games.get(rated_id(t, "fbs"), 0),
            provisional=ratings.games.get(t, 0) < ESTABLISHED_GAMES,
            rank_power=i + 1,
            resume=resumes[t],
            rank_resume=resume_rank[t],
        )
        for i, t in enumerate(power_order)
    ]
    names = {tid: school for tid, school in session.execute(select(Team.id, Team.school))}
    return Rankings(season, as_of, ratings, benchmark, teams, names)
