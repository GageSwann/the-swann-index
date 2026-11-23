"""Which rating runs a rankings page compares (Phase 12.5, #126, #156): the newest run and
its baseline, the last run of the Sunday (Eastern) before the latest Sunday poll."""

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
        (utc(11, 8), utc(11, 2, 5)),  # Sunday Nov 8: the previous Sunday (Nov 1), EST
        (utc(11, 9), utc(11, 2, 5)),  # Monday Nov 9: still Nov 1 (the week's move stays)
        (utc(11, 14), utc(11, 2, 5)),  # Saturday Nov 14: still Nov 1
        (utc(11, 15), utc(11, 9, 5)),  # Sunday Nov 15: now Sunday Nov 8
        (utc(11, 15, 3), utc(11, 2, 5)),  # 3 AM UTC Sunday = 10 PM Saturday Eastern
        (utc(11, 2), utc(10, 26, 4)),  # Mon Nov 2 -> Sun Oct 25 (EDT: midnight = 4 AM UTC)
    ],
)
def test_baseline_cutoff_is_the_end_of_the_previous_weeks_sunday(run_at, cutoff) -> None:
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
    """#91 on Sunday Nov 1; #81 on Sunday Nov 8 shows up 10, and Monday to Saturday keep
    comparing with Nov 1 (#156), so a Tuesday win to #61 shows up 30; Sunday Nov 15 at
    #61 compares with Nov 8: up 20."""
    with sessions.begin() as s:
        s.add(Team(id=1, school="Central Michigan", slug="central-michigan"))
        add_run(s, 1, utc(11, 1), rank=91)  # Sunday Nov 1
    assert arrow(sessions) == (91, None)  # no earlier Sunday this season: no arrow

    steps = [
        (2, utc(11, 3), 75, None),  # Tuesday: the first week has no earlier Sunday
        (3, utc(11, 8), 81, 10),  # Sunday Nov 8: the week's official move (vs. Nov 1)
        (4, utc(11, 9), 81, 10),  # Monday: still vs. Nov 1, not 0 (#156)
        (5, utc(11, 10), 61, 30),  # Tuesday: vs. Nov 1
        (6, utc(11, 15), 61, 20),  # Sunday Nov 15: vs. Sunday Nov 8 (#81)
    ]
    for run_id, run_at, rank, move in steps:
        with sessions.begin() as s:
            add_run(s, run_id, run_at, rank=rank)
        assert arrow(sessions) == (rank, move)


@pytest.mark.db
def test_sunday_edge_cases(sessions) -> None:
    with sessions.begin() as s:
        s.add(Team(id=1, school="Alpha", slug="alpha"))
        add_run(s, 1, utc(10, 31), rank=30)  # Saturday Oct 31
        # No run on Sunday Nov 1 (the job failed): the next week falls back to Saturday's.
        add_run(s, 2, utc(11, 9), rank=20)  # Monday Nov 9
        add_run(s, 3, utc(11, 9, 12), rank=None)  # publish job: no ratings, never shown

    with sessions() as s:
        run, base = run_and_baseline(s, 2026)
        assert (run.id, base.id) == (2, 1)

    with sessions.begin() as s:
        add_run(s, 4, utc(11, 15, 11), rank=25, week=11)  # Sunday Nov 15, first run
        add_run(s, 5, utc(11, 15, 20), rank=24, week=11)  # Sunday Nov 15, rerun later
        add_run(s, 6, utc(11, 22, 11), rank=22, week=12)  # Sunday Nov 22
        add_run(s, 7, utc(11, 23, 11), rank=22, week=12)  # Monday Nov 23

    with sessions() as s:
        run, base = run_and_baseline(s, 2026)
        in_week_10, before_it = run_and_baseline(s, 2026, week=10)
        none = run_and_baseline(s, 2025)
    assert (run.id, base.id) == (7, 5)  # the last run of the previous Sunday
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
