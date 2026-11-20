"""Rebuilt forecasts (#152): shown only for never-published games, never in the Book."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from tsi.db.models import GameOfWeek, Pick, RebuiltForecast
from tsi.db.queries.snapshots import snapshots_for_games, snapshots_for_season
from tsi.services.publish import publish_board
from tsi.services.rebuild import RebuiltDay
from tsi.services.rebuild_store import save_rebuilt_day

from .test_publish_grade import KICKOFF, FakeArtifact, board_game, seed

NOW = datetime(2026, 11, 20, 21, 0, tzinfo=UTC)


def day(as_of: datetime) -> RebuiltDay:
    return RebuiltDay(
        as_of=as_of, ratings=None, board=[board_game(56.0)], sim=None, games_of_week=[]
    )


@pytest.mark.db
def test_rebuilt_forecast_shows_only_for_a_never_published_game(sessions) -> None:
    seed(sessions)
    as_of = KICKOFF - timedelta(hours=6)

    stored = save_rebuilt_day(sessions, day(as_of), FakeArtifact(), store_run=False, now=NOW)

    assert (stored.run_id, stored.forecasts, stored.games_of_week) == (None, 1, 0)
    with sessions() as s:
        snaps = snapshots_for_games(s, [10])[10]
        season = snapshots_for_season(s, KICKOFF.year)
        picks = s.scalars(select(Pick)).all()
    assert len(snaps) == 1 and snaps[0].rebuilt and snaps[0].published_at == as_of
    assert snaps[0].id < 0  # no prediction id: no pick can point at it
    assert season == {} and picks == []  # the Book never sees rebuilt forecasts


@pytest.mark.db
def test_a_published_snapshot_always_wins(sessions) -> None:
    seed(sessions)
    publish_board(sessions, [board_game(56.0)], KICKOFF - timedelta(days=2), FakeArtifact())

    stored = save_rebuilt_day(
        sessions, day(KICKOFF - timedelta(hours=6)), FakeArtifact(), store_run=False, now=NOW
    )

    assert stored.forecasts == 0  # published games are skipped
    with sessions() as s:
        snaps = snapshots_for_games(s, [10])[10]
        rebuilt = s.scalars(select(RebuiltForecast)).all()
    assert rebuilt == [] and [x.rebuilt for x in snaps] == [False]


@pytest.mark.db
def test_games_after_the_next_cutoff_are_left_to_that_day(sessions) -> None:
    seed(sessions)

    stored = save_rebuilt_day(
        sessions, day(KICKOFF - timedelta(days=2)), FakeArtifact(), store_run=False, now=NOW
    )

    assert stored.forecasts == 0
    with sessions() as s:
        assert s.scalars(select(GameOfWeek)).all() == []
