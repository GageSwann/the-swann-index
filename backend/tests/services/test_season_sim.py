import numpy as np
import pytest

from tsi.db.queries.team_info import Record
from tsi.services.season_sim import _projection


def test_projection_adds_simulated_wins_to_the_record() -> None:
    added = np.array([0, 1, 1, 2], dtype=np.int16)  # four simulated seasons, 2 games left

    p = _projection(7, Record(5, 3), left=2, added=added)

    assert p.expected_wins == pytest.approx(6.0)
    assert p.win_dist == pytest.approx([0, 0, 0, 0, 0, 0.25, 0.5, 0.25])  # P(5), P(6), P(7)
    assert (p.team_id, p.remaining, p.record) == (7, 2, Record(5, 3))
