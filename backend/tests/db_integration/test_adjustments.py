"""Manual adjustments: add, list, expire; rows are kept and windows close, never deleted."""

from datetime import UTC, datetime, timedelta

import pytest

from tsi.db.models import Team
from tsi.services.adjust import (
    AdjustmentError,
    NewAdjustment,
    add_adjustment,
    expire_adjustment,
    list_adjustments,
)

NOW = datetime(2026, 11, 3, 15, tzinfo=UTC)


@pytest.fixture
def teams(sessions):
    with sessions.begin() as s:
        s.add(Team(id=1, school="Ohio State", slug="ohio-state"))
    return sessions


def _add(sessions, **kw) -> int:
    new = NewAdjustment(
        **{
            "team_slug": "ohio-state",
            "off_points": -4.0,
            "def_points": 0.0,
            "reason": "QB out",
            **kw,
        }
    )
    return add_adjustment(sessions, new, NOW)


def test_add_defaults_to_now_and_the_rest_of_the_season(teams) -> None:
    adjustment_id = _add(teams)

    with teams() as s:
        (a,) = list_adjustments(s, NOW)
    assert (a.id, a.season, a.school, a.points, a.reason) == (
        adjustment_id,
        2026,
        "Ohio State",
        -4.0,
        "QB out",
    )
    assert a.starts_at == NOW and a.ends_at is None and a.expired_at is None
    assert a.covers(NOW + timedelta(days=60)) and not a.covers(NOW - timedelta(hours=1))


def test_expire_closes_the_window_but_keeps_the_row(teams) -> None:
    adjustment_id = _add(teams)
    later = NOW + timedelta(days=5)

    expire_adjustment(teams, adjustment_id, later)

    with teams() as s:
        assert list_adjustments(s, later + timedelta(minutes=1)) == []
        (a,) = list_adjustments(s, later, include_ended=True)
    assert a.ends_at == later and a.expired_at == later
    assert a.covers(NOW + timedelta(days=4)) and not a.covers(later)
    with pytest.raises(AdjustmentError, match="already ended"):
        expire_adjustment(teams, adjustment_id, later + timedelta(days=1))


def test_expiring_before_the_start_leaves_an_empty_window(teams) -> None:
    adjustment_id = _add(teams, starts_at=NOW + timedelta(days=7))

    expire_adjustment(teams, adjustment_id, NOW)

    with teams() as s:
        (a,) = list_adjustments(s, NOW, include_ended=True)
    assert a.ends_at == a.starts_at and not a.covers(a.starts_at)


@pytest.mark.parametrize(
    ("kw", "message"),
    [
        ({"team_slug": "nope"}, "No team"),
        ({"off_points": 0.0}, "both are zero"),
        ({"def_points": 30.0}, "beyond"),
        ({"reason": "  "}, "reason"),
        ({"ends_at": NOW - timedelta(days=1), "starts_at": NOW - timedelta(days=2)}, "ended"),
        ({"starts_at": NOW + timedelta(days=2), "ends_at": NOW + timedelta(days=1)}, "after"),
    ],
)
def test_rejects_bad_requests(teams, kw, message) -> None:
    with pytest.raises(AdjustmentError, match=message):
        _add(teams, **kw)
    with teams() as s:
        assert list_adjustments(s, NOW, include_ended=True) == []


def test_expire_unknown_id(teams) -> None:
    with pytest.raises(AdjustmentError, match="No adjustment #9"):
        expire_adjustment(teams, 9, NOW)
