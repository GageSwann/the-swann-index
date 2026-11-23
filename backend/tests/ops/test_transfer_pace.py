"""Pace of Neon's network transfer against the free 5 GB and the 80 MB-a-day target."""

from datetime import UTC, datetime

from tsi.ops.neon_api import ProjectUsage
from tsi.ops.transfer_pace import ABOVE_TARGET, ALERT, MB, OK, assess, describe

START, END = datetime(2026, 12, 1, tzinfo=UTC), datetime(2027, 1, 1, tzinfo=UTC)


def usage(used: int, start: datetime | None = START, end: datetime | None = END) -> ProjectUsage:
    return ProjectUsage(used, start, end)


def test_ok_under_the_target() -> None:
    r = assess(usage(500 * MB), datetime(2026, 12, 11, tzinfo=UTC))  # 50 MB a day
    assert r.status == OK
    assert r.per_day_bytes == 50 * MB
    assert r.projected_bytes == 50 * MB * 31
    assert r.period_source == "neon"


def test_above_target_but_not_on_pace_to_go_over() -> None:
    r = assess(usage(1_000 * MB), datetime(2026, 12, 11, tzinfo=UTC))  # 100 MB a day: 3.1 GB
    assert r.status == ABOVE_TARGET


def test_alert_when_on_pace_to_pass_the_limit() -> None:
    r = assess(usage(2_000 * MB), datetime(2026, 12, 11, tzinfo=UTC))  # 200 MB a day: 6.2 GB
    assert r.status == ALERT
    assert "Jan 1" in r.reason


def test_one_heavy_day_early_doesnt_alert_on_pace() -> None:
    r = assess(usage(400 * MB), datetime(2026, 12, 2, 12, tzinfo=UTC))  # 1.5 days in
    assert r.status == ABOVE_TARGET  # pace says 8 GB, but too early to trust


def test_alert_at_80_percent_used_whatever_the_day() -> None:
    r = assess(usage(4_000 * MB), datetime(2026, 12, 2, tzinfo=UTC))
    assert r.status == ALERT
    assert "80%" in r.reason


def test_first_hours_count_as_a_day() -> None:
    r = assess(usage(30 * MB), datetime(2026, 12, 1, 6, tzinfo=UTC))
    assert r.per_day_bytes == 30 * MB


def test_calendar_month_when_neons_dates_dont_bracket_now() -> None:
    now = datetime(2026, 12, 11, tzinfo=UTC)
    short = datetime(2026, 12, 11, 0, 30, tzinfo=UTC)  # a 30-minute window, as in Neon's example
    for u in (
        usage(0, None, None),
        usage(0, START, datetime(2026, 12, 5, tzinfo=UTC)),
        usage(0, now, short),
    ):
        r = assess(u, now)
        assert (r.period_start, r.period_end, r.period_source) == (START, END, "calendar month")


def test_december_rolls_into_january() -> None:
    r = assess(usage(0, None, None), datetime(2026, 12, 31, 23, tzinfo=UTC))
    assert r.period_end == datetime(2027, 1, 1, tzinfo=UTC)


def test_describe_and_json() -> None:
    r = assess(
        usage(480 * MB, datetime(2026, 11, 20, tzinfo=UTC), START),
        datetime(2026, 11, 23, tzinfo=UTC),
    )
    assert describe(r).startswith("Neon transfer above target: averaging 160 MB a day")
    data = r.to_dict()
    assert data["status"] == ABOVE_TARGET and data["used_bytes"] == 480 * MB
