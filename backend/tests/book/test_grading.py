import pytest

from tsi.book.grading import clv_points, clv_prob, grade_pick


def test_spread_grading_home_view() -> None:
    # Home -3: won by 7 covers, won by 3 pushes, won by 1 loses; away +3 is the mirror.
    assert grade_pick("spread", "home", -3.0, -110, 27, 20).result == "win"
    assert grade_pick("spread", "home", -3.0, -110, 23, 20).result == "push"
    assert grade_pick("spread", "home", -3.0, -110, 21, 20).result == "loss"
    assert grade_pick("spread", "away", -3.0, -110, 21, 20).result == "win"


def test_totals_moneyline_and_units() -> None:
    win = grade_pick("total", "over", 50.5, -110, 30, 24)
    assert (win.result, win.units_won) == ("win", pytest.approx(100 / 110))
    assert grade_pick("total", "under", 50.5, -110, 30, 24).units_won == -1.0
    ml = grade_pick("ml", "away", None, 150, 20, 24, stake=2.0)
    assert (ml.result, ml.units_won) == ("win", pytest.approx(3.0))


def test_clv_from_the_picked_sides_view() -> None:
    assert clv_points("spread", "home", -3.0, -4.5) == pytest.approx(1.5)  # line moved our way
    assert clv_points("spread", "away", -3.0, -4.5) == pytest.approx(-1.5)
    assert clv_points("total", "over", 47.5, 50.0) == pytest.approx(2.5)
    assert clv_points("total", "under", 47.5, 50.0) == pytest.approx(-2.5)
    assert clv_prob(150, 0.45) == pytest.approx(0.45 - 0.4)


def test_line_required_for_spreads_and_totals() -> None:
    with pytest.raises(ValueError):
        grade_pick("total", "over", None, -110, 1, 2)
