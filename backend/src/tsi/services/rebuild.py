"""Rebuild days the nightly job never ran (roadmap 13.8, decision #152): the season's start
up to the first nightly run, and the Neon outage (Nov 10-19, 2026).

A rebuilt day is computed exactly like that day's nightly run would have been, through
the same live code, at the nightly cutoff (11:00 UTC) and with only data from games that
kicked off before it (rule 1). What it produces:
- a rating run at the cutoff (stored by `rebuild_store`, `params.job = "rebuild"`), so
  the rating history, ranks and Sunday movement baselines have every day;
- the nightly board (8 days of forecasts, priced like a publish). A game keeps the
  forecast of the last replayed day before its kickoff; rebuilt forecasts are never
  published snapshots (rule 2, #57) and never get picks;
- on Sundays (Eastern), the season sim and that poll week's games of the week (#141).

Nothing here writes, ingests, publishes or grades.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy.orm import Session

from tsi.db.queries.rebuilt import forecast_game_ids
from tsi.db.queries.runs import EASTERN, rating_runs
from tsi.db.queries.schedule import upcoming_games
from tsi.ingest.freshness import current_season
from tsi.model.artifact import ModelArtifact
from tsi.services.board import BoardGame, build_board
from tsi.services.games_of_week import GameOfWeekPick, pick_games_of_week, poll_sunday
from tsi.services.live_inputs import load_live_inputs
from tsi.services.rate import LiveRatings, compute_live_ratings
from tsi.services.season_sim import SeasonProjection, project_season
from tsi.sim.season import DEFAULT_SIMS

CUTOFF = time(11, 0)  # the nightly job's start (UTC), cron-job.org since #126


@dataclass(frozen=True)
class RebuiltDay:
    as_of: datetime  # the cutoff the day is computed at
    ratings: LiveRatings
    board: list[BoardGame]  # the nightly board's window (8 days), priced as published
    sim: SeasonProjection | None  # Sundays only
    games_of_week: list[GameOfWeekPick]  # Sundays only

    def final_forecasts(self) -> list[BoardGame]:
        """Games kicking off before the next day's cutoff: this is the last forecast TSI
        makes before their kickoff, the one a rebuilt game keeps."""
        following = self.as_of + timedelta(days=1)
        return [b for b in self.board if b.forecast.game.start_time <= following]


@dataclass(frozen=True)
class DayPlan:
    day: date
    store_run: bool  # no rating run that day yet; False: forecasts only


def cutoff(day: date) -> datetime:
    return datetime.combine(day, CUTOFF, tzinfo=UTC)


def forecast_day(kickoff: datetime) -> date:
    """The day whose run is the last before this kickoff: cutoff(day) < kickoff <= next."""
    return (kickoff - timedelta(hours=CUTOFF.hour, microseconds=1)).astimezone(UTC).date()


def is_poll_day(as_of: datetime) -> bool:
    """A Sunday (Eastern): the run that picks the games of the week."""
    return poll_sunday(as_of) == as_of.astimezone(EASTERN).date()


def plan(session: Session, season: int, now: datetime) -> list[DayPlan]:
    """Every day to rebuild, oldest first: days from the first game to yesterday without
    a rating run, plus any day whose games have no forecast at all (no published
    snapshot, nothing rebuilt yet), up to today."""
    start = datetime(season, 7, 1, tzinfo=UTC)
    played = [g for g in upcoming_games(session, start, now, with_fcs=True) if g.season == season]
    if not played:
        return []
    have_forecast = forecast_game_ids(session, [g.id for g in played])
    forecast_days = {forecast_day(g.start_time) for g in played if g.id not in have_forecast}
    have_run = {r.run_at.astimezone(UTC).date() for r in rating_runs(session, season)}
    first = forecast_day(played[0].start_time)
    yesterday = (now - timedelta(days=1)).date()
    run_days = {
        first + timedelta(days=i)
        for i in range((yesterday - first).days + 1)
        if first + timedelta(days=i) not in have_run
    }
    days = sorted(d for d in run_days | forecast_days if cutoff(d) < now)
    return [DayPlan(d, d in run_days) for d in days]


def rebuild_day(
    session: Session, day: date, artifact: ModelArtifact, *, sims: int = DEFAULT_SIMS
) -> RebuiltDay:
    return rebuild_at(session, cutoff(day), artifact, sims=sims)


def rebuild_at(
    session: Session, as_of: datetime, artifact: ModelArtifact, *, sims: int = DEFAULT_SIMS
) -> RebuiltDay:
    """What the nightly run at `as_of` computes (any moment; `rebuild_day` uses the cutoff)."""
    live = load_live_inputs(session, current_season(as_of), as_of, artifact)
    ratings = compute_live_ratings(session, as_of, artifact, live)
    board = build_board(session, as_of, artifact, live=live).games
    sim: SeasonProjection | None = None
    picks: list[GameOfWeekPick] = []
    if sims and is_poll_day(as_of) and ratings.rankings.teams:  # sims=0: no sim (verify)
        sim = project_season(
            session, as_of, artifact, sims=sims, live=live, rankings=ratings.rankings
        )
        forecasts = [b.forecast for b in board]
        picks = pick_games_of_week(forecasts, ratings.rankings, sim.game_stakes, as_of)
    return RebuiltDay(as_of=as_of, ratings=ratings, board=board, sim=sim, games_of_week=picks)
