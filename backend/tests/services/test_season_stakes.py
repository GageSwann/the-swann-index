"""Stakes of the coming week's games, from the simulated seasons (decision #141)."""

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from tsi.db.queries.schedule import UpcomingGame
from tsi.services.season_sim import _game_stakes
from tsi.sim.season import SimulatedGames

NOW = datetime(2026, 11, 8, 11, 0, tzinfo=UTC)


def game(gid: int, home: int, away: int, days: float) -> UpcomingGame:
    return UpcomingGame(gid, 2026, 11, "regular", NOW + timedelta(days=days), home, away,
                        "fbs", "fbs", False)  # fmt: skip


def test_stakes_for_games_in_the_window_between_rated_teams() -> None:
    # Teams 10, 20 (FBS) and 30 (not rated). Four simulated seasons.
    upcoming = [game(1, 10, 20, 2), game(2, 10, 30, 3), game(3, 20, 10, 12)]
    margins = np.array([[3.0, 1, 1], [5.0, 1, 1], [-2.0, 1, 1], [-4.0, 1, 1]])
    sim = SimulatedGames(margins, np.zeros((4, 3)), 1.0, np.random.default_rng(0))
    index = {10: 0, 20: 1, 30: 2}
    field = np.array([[0], [0], [1], [0]])  # team 10 in the field in seasons 1, 2 and 4
    champion = {0: np.array([0, 0, 1, 1]), 1: np.array([0, 0, 1, 1])}

    stakes = _game_stakes(upcoming, sim, index, 2, 2, (field, None), champion,
                          NOW + timedelta(days=8))  # fmt: skip

    assert set(stakes) == {1}  # game 2 has an unrated team; game 3 is after the window
    home, away = stakes[1].home, stakes[1].away
    assert home.playoff == pytest.approx(1.0 - 0.5)  # team 10: in 2/2 won, 1/2 lost
    assert home.title == pytest.approx(1.0)
    assert away.playoff == pytest.approx(0.5 - 0.0)  # team 20: in 1/2 when it won, 0/2 lost
    assert away.title == pytest.approx(1.0)
