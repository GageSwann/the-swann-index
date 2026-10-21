from datetime import UTC, datetime, timedelta

import pytest

from tsi.db.queries.snapshots import PickRow, SnapshotRow
from tsi.services.read.common import current_snapshot, pick_view

KICKOFF = datetime(2026, 10, 24, 19, 30, tzinfo=UTC)


def snap(sid: int, published: datetime) -> SnapshotRow:
    return SnapshotRow(
        sid,
        10,
        published,
        30.0,
        24.0,
        -6.0,
        54.0,
        0.65,
        15.4,
        16.4,
        0.04,
        -186,
        186,
        -205,
        170,
        -110,
        -110,
        -110,
        -110,
    )


def pick(**kw) -> PickRow:
    base = dict(
        id=1,
        prediction_id=1,
        market="total",
        side="over",
        line_taken=50.5,
        odds_taken=-110,
        edge=0.03,
        tier=2,
        stake_units=1.0,
        kelly_units=1.2,
        closing_line=52.0,
        closing_odds=None,
        result=None,
        units_won=None,
        graded_at=None,
    )
    return PickRow(**(base | kw))


def test_latest_snapshot_before_kickoff_and_locked_one_after() -> None:
    snaps = [
        snap(1, KICKOFF - timedelta(days=3)),
        snap(2, KICKOFF - timedelta(hours=1)),
        snap(3, KICKOFF + timedelta(minutes=5)),
    ]

    shown, locked = current_snapshot(snaps, KICKOFF, KICKOFF - timedelta(days=1))
    assert (shown.id, locked) == (3, False)  # before kickoff: whatever is newest

    shown, locked = current_snapshot(snaps, KICKOFF, KICKOFF + timedelta(hours=1))
    assert (shown.id, locked) == (2, True)  # after kickoff: the latest pre-kickoff one

    assert current_snapshot([snaps[2]], KICKOFF, KICKOFF + timedelta(hours=1)) == (None, False)
    assert current_snapshot([], None, KICKOFF) == (None, False)


def test_pick_clv_from_the_picked_side() -> None:
    assert pick_view(pick()).clv == pytest.approx(1.5)  # over 50.5, closed 52
    assert pick_view(pick(side="under")).clv == pytest.approx(-1.5)
    assert pick_view(pick(closing_line=None)).clv is None
    ml_pick = pick(market="ml", side="home", line_taken=None, odds_taken=150, closing_odds=120)
    ml = pick_view(ml_pick)
    assert ml.clv == pytest.approx(100 / 220 - 100 / 250)  # price shortened: beat the close
