"""Season splits shared by every backtest: tune on TRAIN, check on VALIDATE (doc 04 §12)."""

from collections.abc import Mapping

from tsi.db.queries.results import GameResult

TRAIN = (2015, 2022)
VALIDATE = (2023, 2025)
FIRST_SCORED_SEASON = 2015  # 2014 only warms ratings up


def is_scored(game: GameResult, closing: Mapping[int, float]) -> bool:
    """Scored set: completed FBS-vs-FBS games with a closing spread, 2015 onward."""
    return game.fbs_vs_fbs and game.season >= FIRST_SCORED_SEASON and game.id in closing
