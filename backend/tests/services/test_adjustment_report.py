"""Raw vs. adjusted scoring: only finished games whose locked snapshot was adjusted count."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from tsi.db.queries.games import GameRow
from tsi.db.queries.snapshots import SnapshotRow
from tsi.services.read.adjustment_report import graded_games, score

KICKOFF = datetime(2026, 10, 24, 19, tzinfo=UTC)
NOW = KICKOFF + timedelta(days=1)


def game(gid: int, home: int, away: int, completed: bool = True) -> GameRow:
    return GameRow(gid, 2026, 9, "regular", KICKOFF, False, 1, 2, False, False, completed,
                   home, away, None)  # fmt: skip


def snap(gid: int, spread: float, total: float, raw: SnapshotRow | None = None,
         published: datetime = KICKOFF - timedelta(days=1)) -> SnapshotRow:  # fmt: skip
    row = SnapshotRow(gid, gid, published, 0, 0, spread, total, 0.5, 15, 16, 0,
                      0, 0, 0, 0, 0, 0, 0, 0)  # fmt: skip
    if raw is None:
        return row
    return replace(row, variant="adjusted", adjustment_ids=[1], raw=raw)


def test_scores_both_rows_and_counts_who_was_closer() -> None:
    games = [game(1, 30, 20), game(2, 17, 24), game(3, 21, 21), game(4, 10, 3)]
    snaps = {
        1: [snap(1, -8.0, 50.0, raw=snap(1, -6.0, 52.0))],  # 10-pt win: adjusted closer
        2: [snap(2, -1.0, 40.0, raw=snap(2, 3.0, 40.0))],  # away by 7: raw closer, flips winner
        3: [snap(3, -2.0, 42.0, raw=snap(3, -2.02, 42.0))],  # tie: same, no winner
        4: [snap(4, -4.0, 20.0)],  # not adjusted: left out
    }

    graded = graded_games(games, snaps, NOW)
    s = score(graded)

    assert s.games == 3
    assert s.raw_mae == pytest.approx((4 + 4 + 2.02) / 3)
    assert s.adjusted_mae == pytest.approx((2 + 8 + 2) / 3)
    assert (s.raw_su, s.adjusted_su) == (1.0, 0.5)  # game 3 excluded (tie)
    assert (s.helped, s.hurt, s.same) == (1, 1, 1)


def test_skips_unfinished_games_and_snapshots_after_kickoff() -> None:
    games = [game(1, 0, 0, completed=False), game(2, 24, 21)]
    late = snap(2, -8.0, 50.0, raw=snap(2, -6.0, 52.0), published=KICKOFF + timedelta(hours=1))
    snaps = {1: [snap(1, -8.0, 50.0, raw=snap(1, -6.0, 52.0))], 2: [late]}

    assert graded_games(games, snaps, NOW) == []
    assert score([]).games == 0 and score([]).raw_mae is None
