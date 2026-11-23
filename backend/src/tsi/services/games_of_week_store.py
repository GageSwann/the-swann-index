"""Save the poll week's games of the week once (decision #141).

The first nightly run of a poll week (Sunday, Eastern, or later if Sunday's run was missed)
picks and stores; later runs that week keep the picks, except that a game added to the
schedule after them can replace one if it's better and the pick hasn't kicked off (#157).
"""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import GameOfWeek
from tsi.db.queries.games_of_week import games_added_since, kickoffs, picks_for
from tsi.services.games_of_week import GameOfWeekPick, pick_order, poll_sunday
from tsi.services.predict import GameForecast

PICK_FIELDS = (
    "game_id",
    "score",
    "quality",
    "closeness",
    "stakes",
    "home_rank",
    "away_rank",
    "home_playoff_swing",
    "away_playoff_swing",
    "home_title_swing",
    "away_title_swing",
)


def save_games_of_week(
    sessions: sessionmaker[Session],
    picks: Sequence[GameOfWeekPick],
    season: int,
    now: datetime,
) -> int:
    """Store this poll week's picks unless it already has some; returns rows written."""
    poll = poll_sunday(now)
    with sessions.begin() as session:
        if not picks or picks_for(session, poll):
            return 0
        session.add_all(
            GameOfWeek(
                season=season,
                poll_date=poll,
                division=p.division,
                ranking_type=p.ranking_type,
                picked_at=now,
                **{f: getattr(p, f) for f in PICK_FIELDS},
            )
            for p in picks
        )
    return len(picks)


def added_games(
    session: Session, forecasts: Sequence[GameForecast], now: datetime
) -> list[GameForecast]:
    """Forecasts of games that first appeared after this poll week's picks were made."""
    stored = picks_for(session, poll_sunday(now))
    if not stored:
        return []
    since = min(p.picked_at for p in stored)
    added = games_added_since(session, [f.game.id for f in forecasts], since)
    return [f for f in forecasts if f.game.id in added]


def upgrade_games_of_week(
    sessions: sessionmaker[Session], challengers: Sequence[GameOfWeekPick], now: datetime
) -> list[GameOfWeekPick]:
    """Replace this week's pick of a division and ranking with the best newly added game
    when it ranks better and the current pick hasn't kicked off; returns the replacements."""
    if not challengers:
        return []
    replaced = []
    with sessions.begin() as session:
        stored = {(p.division, p.ranking_type): p for p in picks_for(session, poll_sunday(now))}
        started = kickoffs(session, [p.game_id for p in stored.values()])
        for new in challengers:
            old = stored.get((new.division, new.ranking_type))
            if old is None or started.get(old.game_id, now) <= now or old.game_id == new.game_id:
                continue
            new_order = pick_order(new.home_rank, new.away_rank, new.closeness, new.game_id)
            old_order = pick_order(old.home_rank, old.away_rank, old.closeness, old.game_id)
            if new_order < old_order:
                for f in PICK_FIELDS:
                    setattr(old, f, getattr(new, f))
                old.picked_at = now
                replaced.append(new)
    return replaced


def needs_picks(session: Session, now: datetime) -> bool:
    """True until this poll week has its games of the week."""
    return not picks_for(session, poll_sunday(now))
