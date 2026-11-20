"""Store a rebuilt day (decision #152): its rating run, its games' forecasts, and on
Sundays the season sim and the poll week's games of the week.

- The rating run is a normal live run (`kind = 'live'`) marked `params.job = "rebuild"`
  with the time it was rebuilt, so history, ranks and Sunday baselines read it as is.
  The first days have no season ranks yet (too few games), only predictive ratings; the
  run is stored anyway (the rating chart skips it) so the plan doesn't revisit the day.
- Forecasts go to `rebuilt_forecasts`, built by the publisher's own `prediction_row`, for
  games that have no published snapshot (published ones always win). Re-running a day
  overwrites its rows (one per game and variant).
- Games of the week: a rebuilt Sunday replaces that poll week's picks only when none
  were stored or they were picked after that Sunday (Eastern; late, like Nov 15's).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import GameOfWeek, RebuiltForecast
from tsi.db.queries.games_of_week import picks_for
from tsi.db.queries.predictions import ADJUSTED, RAW
from tsi.db.queries.rebuilt import published_game_ids
from tsi.db.queries.runs import EASTERN
from tsi.db.upsert import upsert_rows
from tsi.ingest.freshness import current_season
from tsi.model.artifact import ModelArtifact
from tsi.services.board import BoardGame
from tsi.services.games_of_week import poll_sunday
from tsi.services.games_of_week_store import save_games_of_week
from tsi.services.publish import prediction_row
from tsi.services.rate_store import save_live_ratings
from tsi.services.rebuild import RebuiltDay
from tsi.services.sim_store import save_season_sim


@dataclass(frozen=True)
class StoredDay:
    run_id: int | None  # the rebuilt rating run, if one was stored
    forecasts: int  # games given a rebuilt forecast
    sim: bool
    games_of_week: int  # picks written (0: kept the stored ones)


def save_rebuilt_day(
    sessions: sessionmaker[Session],
    day: RebuiltDay,
    artifact: ModelArtifact,
    *,
    store_run: bool,
    now: datetime,
) -> StoredDay:
    run_id = None
    if store_run:
        marker = {"job": "rebuild", "rebuilt_at": now.isoformat()}
        run_id = save_live_ratings(sessions, day.ratings, artifact, extra_params=marker)
    if run_id is not None and day.sim is not None:
        save_season_sim(sessions, run_id, day.sim)
    picks = _replace_games_of_week(sessions, day) if run_id is not None else 0
    return StoredDay(run_id, _save_forecasts(sessions, day, run_id), day.sim is not None, picks)


def _save_forecasts(sessions: sessionmaker[Session], day: RebuiltDay, run_id: int | None) -> int:
    games = day.final_forecasts()
    with sessions.begin() as session:
        published = published_game_ids(session, [b.forecast.game.id for b in games])
        todo = [b for b in games if b.forecast.game.id not in published]
        rows = [
            _row(b, run_id, day.as_of, variant)
            for b in todo
            for variant in ((RAW, ADJUSTED) if b.forecast.adjustment else (RAW,))
        ]
        upsert_rows(session, RebuiltForecast, rows)
    return len(todo)


def _row(b: BoardGame, run_id: int | None, as_of: datetime, variant: str) -> dict[str, Any]:
    row = prediction_row(b, run_id or 0, as_of, variant)
    row["as_of"] = row.pop("published_at")
    row["run_id"] = run_id
    return row


def _replace_games_of_week(sessions: sessionmaker[Session], day: RebuiltDay) -> int:
    if not day.games_of_week:
        return 0
    poll = poll_sunday(day.as_of)
    with sessions.begin() as session:
        stored = picks_for(session, poll)
        if stored and all(p.picked_at.astimezone(EASTERN).date() <= poll for p in stored):
            return 0  # picked on the Sunday by a real run: keep
        session.execute(delete(GameOfWeek).where(GameOfWeek.poll_date == poll))
    return save_games_of_week(sessions, day.games_of_week, current_season(day.as_of), day.as_of)
