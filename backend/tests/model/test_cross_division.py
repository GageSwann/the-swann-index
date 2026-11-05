import pytest

from tsi.model.cross_division import (
    MIN_GAMES,
    NONE,
    CrossDivision,
    CrossGame,
    fit_cross_division,
    is_cross_division,
)


def game(
    bucket: int, margin: float, actual: float, total: float = 50.0, actual_total: float = 50.0
):
    return CrossGame(bucket, margin, actual, total, actual_total)


def test_only_fbs_against_an_individually_rated_fcs_team() -> None:
    assert is_cross_division("fbs", "fcs", 2024)
    assert is_cross_division("fcs", "fbs", 2024)
    assert not is_cross_division("fbs", "fcs", 2021)  # FCS pooled before 2022
    assert not is_cross_division("fbs", "fbs", 2024)
    assert not is_cross_division("fcs", "fcs", 2024)
    assert not is_cross_division("fbs", "ii", 2024)  # lower divisions stay pooled


def test_fit_recovers_each_stage_factor() -> None:
    early = [game(0, 40.0, 30.0, 50.0, 53.0), game(1, -20.0, -15.0, 50.0, 55.0)] * 20  # 0.75
    late = [game(4, 30.0, 27.0, 60.0, 64.0)] * 40  # actual = 0.9 x predicted

    fitted = fit_cross_division(early + late)

    assert fitted.early == pytest.approx(0.75)
    assert fitted.late == pytest.approx(0.9)
    assert fitted.scale(1) == pytest.approx(0.75)
    assert fitted.scale(2) == pytest.approx(0.9)
    assert fitted.total == pytest.approx(4.0)  # totals ran 3, 5 and 4 points low


def test_too_few_games_leave_a_group_unscaled() -> None:
    rows = [game(0, 40.0, 30.0)] * MIN_GAMES + [game(5, 30.0, 20.0)] * (MIN_GAMES - 1)

    assert fit_cross_division(rows) == CrossDivision(0.75, 1.0, 0.0)
    assert fit_cross_division(rows[: MIN_GAMES - 1]).total == 0.0
    assert fit_cross_division([]) == NONE
