"""`/teams` and `/teams/{slug}`: team list, and a team's profile, rating history and schedule."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from tsi.db.queries.games import GameRow, team_games
from tsi.db.queries.runs import latest_rating_run, rating_runs
from tsi.db.queries.snapshots import snapshots_for_games
from tsi.db.queries.team_info import (
    Record,
    StoredRating,
    TeamRef,
    records,
    stored_ratings,
    team_id_by_slug,
    team_refs,
)
from tsi.services.read.common import GameResult, current_snapshot, result_of

RATED_DIVISION = "fbs"


@dataclass(frozen=True)
class TeamRatings:
    rating: float
    off_rating: float
    def_rating: float
    rank_power: int | None
    rank_resume: int | None
    sor: float | None
    games_played: int
    provisional: bool
    predictive_rating: float | None
    predictive_rank: int | None


@dataclass(frozen=True)
class RatingPoint:
    as_of: datetime
    week: int
    rating: float
    rank_power: int | None
    rank_resume: int | None
    predictive_rating: float | None


@dataclass(frozen=True)
class ScheduleGame:
    game_id: int
    kickoff: datetime | None
    week: int
    season_type: str
    opponent: TeamRef
    site: str  # 'home' | 'away' | 'neutral'
    result: GameResult | None  # home/away points as played
    team_points: int | None
    opponent_points: int | None
    outcome: str | None  # 'W' | 'L' | 'T' once final
    projected_team: float | None  # TSI projection, latest (or locked) snapshot
    projected_opponent: float | None
    win_prob: float | None  # TSI win probability for this team
    spread: float | None  # TSI spread from this team's view (negative = favored)


@dataclass(frozen=True)
class TeamProfile:
    team: TeamRef
    season: int
    wins: int
    losses: int
    ties: int
    ratings: TeamRatings | None
    history: list[RatingPoint]
    schedule: list[ScheduleGame]


def team_list(session: Session, season: int) -> list[TeamRef]:
    teams = team_refs(session, season, division=RATED_DIVISION)
    return sorted(teams.values(), key=lambda t: t.school)


def team_profile(session: Session, slug: str, season: int, now: datetime) -> TeamProfile | None:
    team_id = team_id_by_slug(session, slug)
    if team_id is None:
        return None
    games = team_games(session, season, team_id)
    refs = team_refs(
        session, season, {team_id} | {g.home_id for g in games} | {g.away_id for g in games}
    )
    runs = rating_runs(session, season)
    history_rows = stored_ratings(session, [r.id for r in runs], team_id)
    latest = latest_rating_run(session, season)
    rec = records(session, season, now).get(team_id, Record())
    snaps = snapshots_for_games(session, [g.id for g in games])
    return TeamProfile(
        team=refs[team_id],
        season=season,
        wins=rec.wins,
        losses=rec.losses,
        ties=rec.ties,
        ratings=_ratings(history_rows.get(latest.id, [])) if latest else None,
        history=[
            point
            for run in runs
            if (point := _point(run.run_at, run.week, history_rows.get(run.id, []))) is not None
        ],
        schedule=[_schedule_game(g, team_id, refs, snaps.get(g.id, []), now) for g in games],
    )


def _ratings(rows: list[StoredRating]) -> TeamRatings | None:
    season = next((r for r in rows if r.basis == "season"), None)
    if season is None:
        return None
    pred = next((r for r in rows if r.basis == "predictive"), None)
    return TeamRatings(
        rating=season.rating,
        off_rating=season.off_rating,
        def_rating=season.def_rating,
        rank_power=season.rank_power,
        rank_resume=season.rank_resume,
        sor=season.sor,
        games_played=season.games_played,
        provisional=season.provisional,
        predictive_rating=pred.rating if pred else None,
        predictive_rank=pred.rank_power if pred else None,
    )


def _point(as_of: datetime, week: int, rows: list[StoredRating]) -> RatingPoint | None:
    r = _ratings(rows)
    if r is None:
        return None
    return RatingPoint(as_of, week, r.rating, r.rank_power, r.rank_resume, r.predictive_rating)


def _schedule_game(
    g: GameRow, team_id: int, refs: dict[int, TeamRef], snaps, now: datetime
) -> ScheduleGame:
    home = g.home_id == team_id
    sign = 1 if home else -1
    opponent = refs[g.away_id if home else g.home_id]
    result = result_of(g)
    team_pts = opp_pts = outcome = None
    if result is not None:
        team_pts, opp_pts = (
            (result.home_points, result.away_points)
            if home
            else (result.away_points, result.home_points)
        )
        if result.final:
            outcome = "W" if team_pts > opp_pts else "L" if team_pts < opp_pts else "T"
    snap, _ = current_snapshot(snaps, g.start_time, now)
    return ScheduleGame(
        game_id=g.id,
        kickoff=g.start_time,
        week=g.week,
        season_type=g.season_type,
        opponent=opponent,
        site="neutral" if g.neutral else "home" if home else "away",
        result=result,
        team_points=team_pts,
        opponent_points=opp_pts,
        outcome=outcome,
        projected_team=None if snap is None else (snap.proj_home if home else snap.proj_away),
        projected_opponent=None if snap is None else (snap.proj_away if home else snap.proj_home),
        win_prob=None if snap is None else (snap.home_win_prob if home else 1 - snap.home_win_prob),
        spread=None if snap is None else sign * snap.spread,
    )
