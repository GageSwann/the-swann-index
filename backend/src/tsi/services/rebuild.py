"""Rebuild days the nightly job never ran (roadmap 13.8): the season's start up to the
first nightly run, and the Neon outage (Nov 10-19, 2026).

A rebuilt day is computed exactly like that day's nightly run would have been, through
the same live code, at the nightly cutoff (11:00 UTC) and with only data from games that
kicked off before it (rule 1). What it produces:
- a rating run (`model_runs` kind `live`, `params.job = "rebuild"`) at the cutoff, so the
  rating history, ranks and Sunday movement baselines have every day;
- a forecast for each game kicking off before the next day's cutoff: the last forecast
  TSI would have made before that kickoff. Rebuilt forecasts are never published
  snapshots (rule 2, #57): they are stored apart and never get picks;
- on Sundays (Eastern), the season sim and that poll week's games of the week (#141),
  which the Sunday run picks.

Nothing here ingests, publishes or grades. Reading is all this module does; storing is
`rebuild_store.py`.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy.orm import Session

from tsi.db.queries.runs import EASTERN, rating_runs
from tsi.db.queries.schedule import upcoming_games
from tsi.ingest.freshness import current_season
from tsi.model.artifact import ModelArtifact
from tsi.services.board import DEFAULT_DAYS
from tsi.services.games_of_week import GameOfWeekPick, pick_games_of_week, poll_sunday
from tsi.services.live_inputs import load_live_inputs
from tsi.services.predict import GameForecast, forecast_games
from tsi.services.rate import LiveRatings, compute_live_ratings
from tsi.services.season_sim import SeasonProjection, project_season
from tsi.sim.season import DEFAULT_SIMS

CUTOFF = time(11, 0)  # the nightly job's start (UTC), cron-job.org since #126


@dataclass(frozen=True)
class RebuiltDay:
    as_of: datetime  # the cutoff the day is computed at
    ratings: LiveRatings
    board: list[GameForecast]  # the nightly board's window (8 days), as published then
    sim: SeasonProjection | None  # Sundays only
    games_of_week: list[GameOfWeekPick]  # Sundays only

    def final_forecasts(self) -> list[GameForecast]:
        """Games kicking off before the next day's cutoff: this is the last forecast TSI
        makes before their kickoff, the one a rebuilt game keeps."""
        following = self.as_of + timedelta(days=1)
        return [f for f in self.board if f.game.start_time <= following]


def cutoff(day: date) -> datetime:
    return datetime.combine(day, CUTOFF, tzinfo=UTC)


def is_poll_day(as_of: datetime) -> bool:
    """A Sunday (Eastern): the run that picks the games of the week."""
    return poll_sunday(as_of) == as_of.astimezone(EASTERN).date()


def missing_days(session: Session, season: int, first: date, last: date) -> list[date]:
    """Days in [first, last] (UTC) without a stored rating run."""
    have = {r.run_at.astimezone(UTC).date() for r in rating_runs(session, season)}
    days = (first + timedelta(days=i) for i in range((last - first).days + 1))
    return [d for d in days if d not in have]


def rebuild_day(
    session: Session, day: date, artifact: ModelArtifact, *, sims: int = DEFAULT_SIMS
) -> RebuiltDay:
    return rebuild_at(session, cutoff(day), artifact, sims=sims)


def rebuild_at(
    session: Session, as_of: datetime, artifact: ModelArtifact, *, sims: int = DEFAULT_SIMS
) -> RebuiltDay:
    """What the nightly run at `as_of` computes (any moment; `rebuild_day` uses the cutoff)."""
    season = current_season(as_of)
    live = load_live_inputs(session, season, as_of, artifact)
    ratings = compute_live_ratings(session, as_of, artifact, live)
    # The nightly board's window (8 days): the games of the week choose from it.
    games = [
        g
        for g in upcoming_games(session, as_of, as_of + timedelta(days=DEFAULT_DAYS), with_fcs=True)
        if g.season == season
    ]
    forecasts = forecast_games(games, live, artifact)
    sim: SeasonProjection | None = None
    picks: list[GameOfWeekPick] = []
    if is_poll_day(as_of):
        sim = project_season(
            session, as_of, artifact, sims=sims, live=live, rankings=ratings.rankings
        )
        picks = pick_games_of_week(forecasts, ratings.rankings, sim.game_stakes, as_of)
    return RebuiltDay(as_of=as_of, ratings=ratings, board=forecasts, sim=sim, games_of_week=picks)
