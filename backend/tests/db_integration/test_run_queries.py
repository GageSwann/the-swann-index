"""Which rating runs a rankings page compares: the newest run and the one a week before."""

from datetime import UTC, datetime, timedelta

from tsi.db.models import ModelRun, Team, TeamRating
from tsi.db.queries.runs import run_and_week_ago

NOW = datetime(2026, 10, 26, 16, 40, tzinfo=UTC)


def add_run(session, run_id: int, run_at: datetime, week: int, rated: bool = True) -> None:
    session.add(
        ModelRun(
            id=run_id,
            kind="live",
            season=2026,
            week=week,
            season_type="regular",
            run_at=run_at,
            model_version="tsi-test",
            params={},
        )
    )
    session.flush()
    if rated:
        session.add(
            TeamRating(run_id=run_id, team_id=1, rating=1.0, off_rating=0.5, def_rating=0.5)
        )


def test_compares_with_the_newest_run_at_least_six_days_older(sessions) -> None:
    with sessions.begin() as s:
        s.add(Team(id=1, school="Alpha", slug="alpha"))
        add_run(s, 1, NOW - timedelta(days=8), week=7)
        add_run(s, 2, NOW - timedelta(days=6, hours=2), week=8)  # a week ago, give or take
        add_run(s, 3, NOW - timedelta(days=1), week=8)  # yesterday: too recent
        add_run(s, 4, NOW, week=9)
        add_run(s, 5, NOW + timedelta(minutes=5), week=9, rated=False)  # publish job: no ratings

    with sessions() as s:
        run, week_ago = run_and_week_ago(s, 2026)
        in_week_8, before_it = run_and_week_ago(s, 2026, week=8)

    assert (run.id, week_ago.id) == (4, 2)
    # Within week 8 the newest run is yesterday's; nothing is six days older than it but run 1.
    assert (in_week_8.id, before_it.id) == (3, 1)


def test_no_comparison_without_an_older_run(sessions) -> None:
    with sessions.begin() as s:
        s.add(Team(id=1, school="Alpha", slug="alpha"))
        add_run(s, 1, NOW - timedelta(days=2), week=8)
        add_run(s, 2, NOW, week=9)

    with sessions() as s:
        run, week_ago = run_and_week_ago(s, 2026)
        none = run_and_week_ago(s, 2025)

    assert run.id == 2 and week_ago is None
    assert none == (None, None)
