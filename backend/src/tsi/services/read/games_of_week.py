"""`/games-of-week`: this poll week's FBS and FCS games of the week (decision #141)."""

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.orm import Session

from tsi.db.queries.games import season_games
from tsi.db.queries.games_of_week import latest_poll_date, picks_for
from tsi.services.games_of_week import poll_sunday
from tsi.services.read.games import GameSummary, game_summaries


@dataclass(frozen=True)
class GameOfWeekView:
    division: str  # fbs / fcs
    ranking_type: str  # power / resume
    game: GameSummary  # with TSI's current prediction and the market, as on the week board
    score: float
    quality: float  # 0..1: both teams' ranks in the chosen ranking
    closeness: float  # 0..1: TSI's win probability near 50%
    stakes: float  # 0..1: playoff and conference-title odds riding on the result
    home_rank: int | None  # rank in the chosen ranking when picked
    away_rank: int | None
    home_playoff_swing: float | None  # P(make the field | win) - P(... | loss)
    away_playoff_swing: float | None
    home_title_swing: float | None  # the same for the conference title
    away_title_swing: float | None


@dataclass(frozen=True)
class GamesOfWeek:
    poll_date: date | None  # the poll week's Sunday; None before the first pick
    picked_at: datetime | None
    picks: list[GameOfWeekView]  # FBS then FCS, Power then Résumé; missing when none qualified


def games_of_week(session: Session, now: datetime) -> GamesOfWeek:
    poll = latest_poll_date(session, poll_sunday(now))
    if poll is None:
        return GamesOfWeek(None, None, [])
    rows = picks_for(session, poll)
    season = rows[0].season
    summaries = {
        s.id: s
        for s in game_summaries(
            session, season_games(session, season, [r.game_id for r in rows]), now
        )
    }
    picks = [
        GameOfWeekView(
            division=r.division,
            ranking_type=r.ranking_type,
            game=summaries[r.game_id],
            score=r.score,
            quality=r.quality,
            closeness=r.closeness,
            stakes=r.stakes,
            home_rank=r.home_rank,
            away_rank=r.away_rank,
            home_playoff_swing=r.home_playoff_swing,
            away_playoff_swing=r.away_playoff_swing,
            home_title_swing=r.home_title_swing,
            away_title_swing=r.away_title_swing,
        )
        for r in rows
        if r.game_id in summaries
    ]
    return GamesOfWeek(poll, rows[0].picked_at, picks)
