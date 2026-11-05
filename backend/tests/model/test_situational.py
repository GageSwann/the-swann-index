from datetime import UTC, datetime, timedelta

import pytest

from tsi.model.situational import NONE, features, fit_situational, rest_days

SAT = datetime(2026, 10, 3, 19, tzinfo=UTC)


def test_rest_days_count_from_the_previous_game_this_season() -> None:
    kickoffs = [SAT - timedelta(days=14), SAT - timedelta(days=7), SAT, SAT + timedelta(days=7)]

    assert rest_days(kickoffs, SAT) == pytest.approx(7.0)
    assert rest_days(kickoffs, SAT - timedelta(days=14)) is None  # season opener


def test_features_are_home_minus_away() -> None:
    assert features(14.0, 7.0) == (7.0, 1.0, 0.0)  # home off a bye
    assert features(5.0, 7.0) == (-2.0, 0.0, 1.0)  # home on a Thursday after a Saturday
    assert features(7.0, 20.0) == (-7.0, -1.0, 0.0)  # gap capped at 7 days
    assert features(None, 13.0) == (0.0, -1.0, 0.0)  # opener vs. a team off a bye


def test_fit_recovers_a_bye_effect() -> None:
    rows = [((0.0, 1.0, 0.0), 2.0), ((0.0, -1.0, 0.0), -2.0)] * 200 + [((0.0, 0.0, 0.0), 0.5)] * 400

    fitted = fit_situational(rows)

    assert fitted.coefs[1] == pytest.approx(2.0 * 400 / (400 + 50))  # light ridge shrink
    assert fitted.shift((0.0, 1.0, 0.0)) == pytest.approx(fitted.coefs[1])
    assert fit_situational([]) == NONE
