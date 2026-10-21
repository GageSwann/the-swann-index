"""`/matchup`: on-demand prediction for any two teams, as of now (hypothetical games).

Same path as the published board (services/predict.py) with today's live inputs.
Loading those takes ~1 s of queries, and the data changes once a day, so they are
cached in-process for an hour (one entry per season).
"""

import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from sqlalchemy.orm import Session

from tsi.book.pricing import GameMarkets, price_game
from tsi.db.queries.schedule import UpcomingGame
from tsi.db.queries.team_info import TeamRef, team_id_by_slug, team_refs
from tsi.ingest.freshness import current_season
from tsi.model.artifact import ModelArtifact, load_artifact
from tsi.services.live_inputs import LiveInputs, load_live_inputs
from tsi.services.predict import forecast_game

CACHE_TTL = timedelta(hours=1)
_cache: dict[int, tuple[datetime, LiveInputs]] = {}
_lock = threading.Lock()


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
    markets: GameMarkets


class UnknownTeamError(LookupError):
    pass


def matchup(session: Session, home: str, away: str, neutral: bool, now: datetime) -> Matchup:
    season = current_season(now)
    ids = {slug: team_id_by_slug(session, slug) for slug in (home, away)}
    missing = [slug for slug, tid in ids.items() if tid is None]
    if missing:
        raise UnknownTeamError(", ".join(missing))
    refs = team_refs(session, season, ids.values())
    h, a = refs[ids[home]], refs[ids[away]]
    artifact = _artifact()
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
    live = _live_inputs(session, season, now, artifact)
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
        markets=price_game(dist),
    )


@lru_cache(maxsize=1)
def _artifact() -> ModelArtifact:
    return load_artifact()


def _live_inputs(
    session: Session, season: int, now: datetime, artifact: ModelArtifact
) -> LiveInputs:
    with _lock:
        hit = _cache.get(season)
        if hit and now - hit[0] < CACHE_TTL:
            return hit[1]
    live = load_live_inputs(session, season, now, artifact)
    with _lock:
        _cache[season] = (datetime.now(UTC), live)
    return live
