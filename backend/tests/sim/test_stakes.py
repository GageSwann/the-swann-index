"""Stakes of a single game, read from the simulated seasons (decision #141)."""

import numpy as np
import pytest

from tsi.sim.stakes import TeamStakes, stakes_value, swing, team_stakes


def test_swing_compares_seasons_won_and_lost() -> None:
    won = np.array([True, True, True, False, False])
    made = np.array([True, True, False, False, True])
    assert swing(won, made) == pytest.approx(2 / 3 - 1 / 2)


def test_swing_is_zero_when_the_game_never_goes_the_other_way() -> None:
    assert swing(np.ones(4, dtype=bool), np.array([True, False, True, False])) == 0.0


def test_team_stakes_reads_field_and_champion() -> None:
    won = np.array([True, True, False, False])
    field = np.array([[7, 1], [7, 2], [1, 2], [2, 7]])  # team 7 in, in, out, in
    champion = np.array([7, 7, 3, 3])
    s = team_stakes(7, won, field, champion)
    assert s.playoff == pytest.approx(1.0 - 0.5)
    assert s.title == pytest.approx(1.0)


def test_team_stakes_without_field_or_conference() -> None:
    assert team_stakes(1, np.array([True, False]), None, None) == TeamStakes(None, None)


def test_stakes_value_counts_half_the_title_and_ignores_negative_swings() -> None:
    assert stakes_value(TeamStakes(0.3, 0.4)) == pytest.approx(0.5)
    assert stakes_value(TeamStakes(-0.1, None)) == 0.0
    assert stakes_value(TeamStakes(0.9, 0.9)) == 1.0
