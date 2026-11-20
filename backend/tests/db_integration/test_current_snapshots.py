"""`current_snapshots` loads only the snapshot pages show, as `current_snapshot` picks it (#155)."""

from datetime import timedelta

import pytest

from tsi.db.queries.snapshots import current_snapshots, snapshots_for_games
from tsi.services.publish import publish_board
from tsi.services.read.common import current_snapshot

from .test_publish_adjusted import adjusted_game
from .test_publish_grade import KICKOFF, FakeArtifact, board_game, seed


@pytest.mark.db
@pytest.mark.parametrize("now", [KICKOFF - timedelta(days=1), KICKOFF + timedelta(hours=3)])
def test_current_snapshots_match_current_snapshot(sessions, now) -> None:
    seed(sessions)
    publish_board(sessions, [board_game(56.0)], KICKOFF - timedelta(days=5), FakeArtifact())
    publish_board(sessions, [adjusted_game(52.0)], KICKOFF - timedelta(days=2), FakeArtifact())
    # Published after kickoff: never the one shown once the game has started.
    publish_board(sessions, [board_game(60.0)], KICKOFF + timedelta(hours=1), FakeArtifact())

    with sessions() as s:
        everything = snapshots_for_games(s, [10])[10]
        shown = current_snapshots(s, [10], now)[10]

    want, _ = current_snapshot(everything, KICKOFF, now)
    assert shown == [want]
    if now > KICKOFF:  # the locked one: the adjusted publish, with its raw twin attached
        assert want.variant == "adjusted" and want.raw is not None
