import numpy as np
import pytest

from tsi.db.queries.team_info import Record
from tsi.services.season_sim import _projection


def test_projection_adds_simulated_wins_to_the_record() -> None:
    added = np.array([0, 1, 1, 2], dtype=np.int16)  # four simulated seasons, 2 games left

    p = _projection(7, "SEC", Record(5, 3), left=2, added=added, win_out=0.25, odds=(0.4, 0.1))

    assert p.expected_wins == pytest.approx(6.0)
    assert p.win_dist == pytest.approx([0, 0, 0, 0, 0, 0.25, 0.5, 0.25])  # P(5), P(6), P(7)
    assert (p.team_id, p.remaining, p.record) == (7, 2, Record(5, 3))
    assert (p.conference, p.title_game_prob, p.conference_title_prob) == ("SEC", 0.4, 0.1)


def test_independents_have_no_title_odds() -> None:
    p = _projection(1, "FBS Independents", Record(6, 1), 0, np.zeros(3, np.int16), 1.0, odds=None)

    assert (p.title_game_prob, p.conference_title_prob) == (None, None)
