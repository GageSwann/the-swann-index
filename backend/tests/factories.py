"""Small builders for test objects shared across test modules."""

from datetime import UTC, datetime

from tsi.backtest.walk_forward import Pick
from tsi.db.queries.results import GameResult


def make_game(gid: int, home_points: int, away_points: int, season: int = 2024) -> GameResult:
    """A completed FBS-vs-FBS game: home team 1, away team 2, non-neutral."""
    kickoff = datetime(season, 9, 7, tzinfo=UTC)
    return GameResult(gid, season, kickoff, 1, 2, "fbs", "fbs", False, home_points, away_points)


def make_pick(
    gid: int,
    home_points: int,
    away_points: int,
    *,
    margin: float = 0.0,
    total: float = 0.0,
    season: int = 2024,
) -> Pick:
    """A walk-forward pick with the given predictive margin and total (established, bucket 4)."""
    game = make_game(gid, home_points, away_points, season)
    return Pick(game, margin, margin, total, True, 4, (), ())
