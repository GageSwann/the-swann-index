"""`/matchup`: on-demand prediction for any two teams, as of now (hypothetical games).

Same path as the published board (services/predict.py) with today's live inputs.
Loading those takes ~1 s of queries, and the data changes once a day, so they are
cached in-process for an hour (one entry per season). Loads are single-flight: on a cold
cache one request loads while concurrent ones wait, before touching the database, so a
burst of requests (e.g. a site build) can't exhaust the connection pool.
"""

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache

from sqlalchemy.orm import Session

from tsi.book.pricing import GameMarkets, price_game
from tsi.db.queries.schedule import UpcomingGame
from tsi.db.queries.team_info import TeamRef, team_ids_by_slug, team_refs
from tsi.ingest.freshness import current_season
from tsi.model.artifact import ModelArtifact, load_artifact
from tsi.services.live_inputs import LiveInputs, load_live_inputs
from tsi.services.predict import forecast_game

CACHE_TTL = timedelta(hours=1)
_cache: dict[int, tuple[datetime, LiveInputs]] = {}
_lock = threading.Lock()  # guards _cache
_load_lock = threading.Lock()  # one loader at a time


@dataclass(frozen=True)
class Matchup:
    home: TeamRef
    away: TeamRef
    neutral: bool
    as_of: datetime  # data as of (live inputs load time)
    proj_home: float
    proj_away: float
    spread: float  # home view, negative = home favored
    total: float
    home_win_prob: float
    sigma_margin: float  # spread of the score distribution (for the margin chart)
    sigma_total: float
    markets: GameMarkets


class UnknownTeamError(LookupError):
    pass


def matchup(session: Session, home: str, away: str, neutral: bool, now: datetime) -> Matchup:
    season = current_season(now)
    artifact = _artifact()
    live = _live_inputs(session, season, now, artifact)  # first: waiters hold no connection
    ids = team_ids_by_slug(session, (home, away))
    missing = [slug for slug in (home, away) if slug not in ids]
    if missing:
        raise UnknownTeamError(", ".join(missing))
    refs = team_refs(session, season, ids.values())
    h, a = refs[ids[home]], refs[ids[away]]
    game = UpcomingGame(
        id=0,
        season=season,
        week=0,
        season_type="regular",
        start_time=now,
        home_id=h.id,
        away_id=a.id,
        home_div=h.division or "unknown",
        away_div=a.division or "unknown",
        neutral=neutral,
    )
    dist = forecast_game(game, live, artifact).distribution
    return Matchup(
        home=h,
        away=a,
        neutral=neutral,
        as_of=live.as_of,  # when the inputs were loaded: stable while cached (ETag)
        proj_home=dist.home_points,
        proj_away=dist.away_points,
        spread=-dist.margin,
        total=dist.total,
        home_win_prob=dist.home_win_prob,
        sigma_margin=dist.sigma_margin,
        sigma_total=dist.sigma_total,
        markets=price_game(dist),
    )


@lru_cache(maxsize=1)
def _artifact() -> ModelArtifact:
    return load_artifact()


def _live_inputs(
    session: Session, season: int, now: datetime, artifact: ModelArtifact
) -> LiveInputs:
    if (hit := _cached(season, now)) is not None:
        return hit
    with _load_lock:
        if (hit := _cached(season, now)) is not None:  # loaded while this request waited
            return hit
        live = load_live_inputs(session, season, now, artifact)
        with _lock:
            _cache[season] = (now, live)  # same clock as the freshness check
        return live


def _cached(season: int, now: datetime) -> LiveInputs | None:
    with _lock:
        hit = _cache.get(season)
    return hit[1] if hit and now - hit[0] < CACHE_TTL else None
