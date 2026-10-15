import pytest

from tsi.backtest.evaluate import ScoredGame, summarize, summarize_by_season, summarize_period

GAMES = [
    ScoredGame(2015, pred_margin=7, home_win_prob=0.7, actual_margin=10, market_margin=6),
    ScoredGame(2015, pred_margin=-3, home_win_prob=0.4, actual_margin=4, market_margin=1),
    ScoredGame(2023, pred_margin=10, home_win_prob=0.8, actual_margin=14, market_margin=12),
]


def test_summary_compares_model_with_market() -> None:
    s = summarize("x", GAMES[:2])

    assert s.games == 2
    assert s.mae == pytest.approx((3 + 7) / 2)
    assert s.market_mae == pytest.approx((4 + 3) / 2)
    assert s.su_accuracy == pytest.approx(0.5)
    assert s.market_su_accuracy == pytest.approx(1.0)


def test_grouping_by_season_and_period() -> None:
    assert [s.label for s in summarize_by_season(GAMES)] == ["2015", "2023"]
    assert summarize_period("train", GAMES, 2015, 2022).games == 2
