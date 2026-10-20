import pytest

from tsi.model.totals import LEVEL_SHRINK, project_scores, scoring_level


def test_scores_reproduce_margin_and_total() -> None:
    home, away = project_scores(margin=-3.5, total=51.0)

    assert home - away == pytest.approx(-3.5)
    assert home + away == pytest.approx(51.0)


def test_scoring_level_moves_from_last_season_to_this_one() -> None:
    assert scoring_level(None, 55.0, 0) == 55.0
    assert scoring_level(50.0, 55.0, LEVEL_SHRINK) == pytest.approx(52.5)
    assert scoring_level(50.0, 55.0, 100 * LEVEL_SHRINK) == pytest.approx(50.0, abs=0.1)
