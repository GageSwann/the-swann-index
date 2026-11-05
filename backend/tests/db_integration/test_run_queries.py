"""Which rating runs a rankings page compares (Phase 12.5, #126): the newest run and its
baseline, the last run of the most recent Sunday (Eastern) before the newest run's day."""

from datetime import UTC, datetime

import pytest

from tsi.db.models import ModelRun, Team, TeamRating
from tsi.db.queries.runs import baseline_cutoff, run_and_baseline


def utc(month: int, day: int, hour: int = 11, minute: int = 0) -> datetime:
    return datetime(2026, month, day, hour, minute, tzinfo=UTC)


# November 2026: Sun 1 (daylight saving time ends at 2 AM), Sun 8, Sun 15.
@pytest.mark.parametrize(
    ("run_at", "cutoff"),
    [
        (utc(11, 2), utc(11, 2, 5)),  # Monday: the end of yesterday (Sun Nov 1), EST
        (utc(11, 7), utc(11, 2, 5)),  # Saturday: still that Sunday
        (utc(11, 8), utc(11, 2, 5)),  # Sunday Nov 8: the previous Sunday, not today
        (utc(11, 9), utc(11, 9, 5)),  # Monday Nov 9: Sunday Nov 8
        (utc(11, 8, 3), utc(11, 2, 5)),  # 3 AM UTC Sunday = 10 PM Saturday Eastern
        (utc(11, 1, 11), utc(10, 26, 4)),  # Sun Nov 1 -> Sun Oct 25 (EDT: midnight = 4 AM UTC)
    ],
)
def test_baseline_cutoff_is_the_end_of_the_last_sunday_before_today(run_at, cutoff) -> None:
    assert baseline_cutoff(run_at) == cutoff


def add_run(session, run_id: int, run_at: datetime, rank: int | None = 50, week: int = 10) -> None:
    session.add(
        ModelRun(id=run_id, kind="live", season=2026, week=week, season_type="regular",
                 run_at=run_at, model_version="tsi-test", params={})
    )  # fmt: skip
    session.flush()
    if rank is not None:  # a publish-only run stores no ratings
        session.add(TeamRating(run_id=run_id, team_id=1, rating=1.0, off_rating=0.5,
                               def_rating=0.5, rank_power=rank))  # fmt: skip


def arrow(sessions) -> tuple[int, int | None]:
    """(newest run's rank, its move vs. the baseline: + = up), as the rankings page shows."""
    with sessions() as s:
        run, base = run_and_baseline(s, 2026)
        ranks = {r.run_id: r.rank_power for r in s.query(TeamRating)}
    return ranks[run.id], (ranks[base.id] - ranks[run.id]) if base else None


@pytest.mark.db
def test_owners_central_michigan_example(sessions) -> None:
    """#91 on Sunday; wins Tuesday to #75 (up 16); Saturday's results move it to #81 (up 10);
    that Sunday shows up 10 and #81 becomes the baseline; it wins again to #61: up 20."""
    with sessions.begin() as s:
        s.add(Team(id=1, school="Central Michigan", slug="central-michigan"))
        add_run(s, 1, utc(11, 1), rank=91)  # Sunday Nov 1
    assert arrow(sessions) == (91, None)  # no earlier Sunday this season: no arrow

    steps = [
        (2, utc(11, 3), 75, 16),  # Tuesday: vs. Sunday Nov 1
        (3, utc(11, 7), 81, 10),  # Saturday: still vs. Sunday Nov 1
        (4, utc(11, 8), 81, 10),  # Sunday Nov 8: the week's official move (vs. Nov 1)
        (5, utc(11, 10), 61, 20),  # Tuesday: vs. Sunday Nov 8 (#81), not +30
    ]
    for run_id, run_at, rank, move in steps:
        with sessions.begin() as s:
            add_run(s, run_id, run_at, rank=rank)
        assert arrow(sessions) == (rank, move)


@pytest.mark.db
def test_sunday_edge_cases(sessions) -> None:
    with sessions.begin() as s:
        s.add(Team(id=1, school="Alpha", slug="alpha"))
        add_run(s, 1, utc(11, 7), rank=30)  # Saturday Nov 7
        # No run on Sunday Nov 8 (the job failed): Monday falls back to Saturday's.
        add_run(s, 2, utc(11, 9), rank=20)
        add_run(s, 3, utc(11, 9, 12), rank=None)  # publish job: no ratings, never shown

    with sessions() as s:
        run, base = run_and_baseline(s, 2026)
        assert (run.id, base.id) == (2, 1)

    with sessions.begin() as s:
        add_run(s, 4, utc(11, 15, 11), rank=25, week=11)  # Sunday Nov 15, first run
        add_run(s, 5, utc(11, 15, 20), rank=24, week=11)  # Sunday Nov 15, rerun later
        add_run(s, 6, utc(11, 16, 11), rank=22, week=11)  # Monday

    with sessions() as s:
        run, base = run_and_baseline(s, 2026)
        in_week_10, before_it = run_and_baseline(s, 2026, week=10)
        none = run_and_baseline(s, 2025)
    assert (run.id, base.id) == (6, 5)  # the last run of that Sunday
    assert (in_week_10.id, before_it.id) == (2, 1)  # a past week has its own baseline
    assert none == (None, None)


@pytest.mark.db
def test_a_late_saturday_run_is_not_a_sunday_run(sessions) -> None:
    with sessions.begin() as s:
        s.add(Team(id=1, school="Alpha", slug="alpha"))
        add_run(s, 1, utc(11, 1), rank=40)  # Sunday Nov 1
        add_run(s, 2, utc(11, 8, 3), rank=35)  # 10 PM Saturday Nov 7 Eastern
        add_run(s, 3, utc(11, 8, 11), rank=30)  # Sunday Nov 8

    with sessions() as s:
        run, base = run_and_baseline(s, 2026)
    assert (run.id, base.id) == (3, 1)  # Sunday Nov 8 compares with Sunday Nov 1
