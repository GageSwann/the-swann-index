import pytest

from tsi.model.adjust import GameAdjustment, adjust_distribution
from tsi.model.distribution import DistributionParams
from tsi.model.lopsided import (
    MIN_GAMES,
    MIN_POINTS,
    NONE,
    THRESHOLD,
    Lopsided,
    TotalGame,
    applies,
    fit_lopsided,
    floored_total,
)

PARAMS = DistributionParams(15.4, 16.4, 0.12, 0.0074)


def test_bump_starts_past_the_threshold_on_either_side() -> None:
    lop = Lopsided(slope=0.2)
    assert lop.bump(THRESHOLD, 50.0) == 50.0
    assert lop.bump(-10.0, 50.0) == 50.0
    assert lop.bump(THRESHOLD + 30, 50.0) == pytest.approx(56.0)
    assert lop.bump(-(THRESHOLD + 30), 50.0) == pytest.approx(56.0)  # away favorite too
    assert NONE.bump(70.0, 50.0) == 50.0


def test_bump_is_for_games_with_an_individually_rated_fcs_team() -> None:
    assert applies("fbs", "fcs", 2024) and applies("fcs", "fbs", 2024)
    assert applies("fcs", "fcs", 2024)
    assert not applies("fbs", "fbs", 2024)  # FBS games keep their totals (the Book, #132)
    assert not applies("fbs", "fcs", 2021)  # FCS pooled before 2022
    assert not applies("fbs", "ii", 2024)


def test_fit_recovers_the_slope() -> None:
    # Totals ran low by 0.25 points per point of margin past the threshold.
    games = [TotalGame(m, 50.0, 50.0 + 0.25 * max(0.0, abs(m) - THRESHOLD)) for m in range(-60, 61)]

    assert fit_lopsided(games).slope == pytest.approx(0.25)


def test_too_few_games_or_no_lopsided_games_fit_nothing() -> None:
    assert fit_lopsided([TotalGame(50.0, 40.0, 60.0)] * (MIN_GAMES - 1)) == NONE
    assert fit_lopsided([TotalGame(5.0, 40.0, 60.0)] * MIN_GAMES) == NONE


def test_floor_keeps_the_underdog_at_min_points() -> None:
    assert floored_total(53.5, 52.8) == pytest.approx(53.5 + 2 * MIN_POINTS)  # Merrimack, -0.33
    assert floored_total(-53.5, 52.8) == pytest.approx(53.5 + 2 * MIN_POINTS)
    assert floored_total(7.0, 50.0) == 50.0  # untouched when the underdog has points


def test_every_distribution_has_no_negative_projected_score() -> None:
    for margin in (-80.0, -53.5, -10.0, 0.0, 10.0, 53.5, 80.0):
        for total in (-5.0, 0.0, 20.0, 52.8):
            dist = PARAMS.for_game(margin, total)
            assert min(dist.home_points, dist.away_points) >= MIN_POINTS - 1e-9
            assert dist.margin == margin  # the floor never moves the margin


def test_manual_adjustments_cannot_push_a_score_below_the_floor() -> None:
    raw = PARAMS.for_game(-40.0, 50.0)  # away projected 45, home 5
    # Home offense -10: home would project -5 without the floor.
    adjusted = adjust_distribution(raw, GameAdjustment(ids=(1,), home_off=-10.0), PARAMS)

    assert adjusted.home_points == pytest.approx(MIN_POINTS)
