"""Save the poll week's games of the week once (decision #141).

The first nightly run of a poll week (Sunday, Eastern, or later if Sunday's run was missed)
picks and stores; later runs that week leave the picks alone, so they hold all week.
"""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import GameOfWeek
from tsi.db.queries.games_of_week import picks_for
from tsi.services.games_of_week import GameOfWeekPick, poll_sunday


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
                game_id=p.game_id,
                picked_at=now,
                score=p.score,
                quality=p.quality,
                closeness=p.closeness,
                stakes=p.stakes,
                home_rank=p.home_rank,
                away_rank=p.away_rank,
                home_playoff_swing=p.home_playoff_swing,
                away_playoff_swing=p.away_playoff_swing,
                home_title_swing=p.home_title_swing,
                away_title_swing=p.away_title_swing,
            )
            for p in picks
        )
    return len(picks)


def needs_picks(session: Session, now: datetime) -> bool:
    """True until this poll week has its games of the week."""
    return not picks_for(session, poll_sunday(now))
