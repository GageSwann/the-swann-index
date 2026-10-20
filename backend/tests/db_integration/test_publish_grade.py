"""Publish -> dedupe -> immutability -> lock -> grade, against a throwaway schema."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.exc import DBAPIError

from tsi.book.consensus import ConsensusLine
from tsi.book.edges import EdgeShrink, game_edges
from tsi.book.picks import choose_picks
from tsi.book.pricing import price_game
from tsi.db.models import Game, MarketLine, Pick, Prediction, Team
from tsi.db.queries.schedule import UpcomingGame
from tsi.model.distribution import DistributionParams
from tsi.services.board import BoardGame
from tsi.services.grade import grade_picks
from tsi.services.predict import GameForecast
from tsi.services.publish import publish_board

KICKOFF = datetime(2026, 10, 24, 19, 30, tzinfo=UTC)
PARAMS = DistributionParams(15.4, 16.4, 0.12, 0.0075)
MARKET = ConsensusLine(-3.0, 45.5, -150, 130, 0.58, 2)


class FakeArtifact:
    version = "tsi-test"
    fitted_seasons = (2015, 2025)
    edge_shrink = EdgeShrink(0.07, 0.32)


def board_game(total: float) -> BoardGame:
    game = UpcomingGame(10, 2026, 9, "regular", KICKOFF, 1, 2, "fbs", "fbs", False)
    dist = PARAMS.for_game(4.0, total)
    edges = game_edges(dist, MARKET, FakeArtifact.edge_shrink)
    forecast = GameForecast(game, 4, dist)
    return BoardGame(forecast, price_game(dist), MARKET, edges, choose_picks(edges))


def seed(sessions) -> None:
    with sessions.begin() as s:
        s.add_all([Team(id=1, school="Home", slug="home"), Team(id=2, school="Away", slug="away")])
        s.flush()
        s.add(
            Game(
                id=10,
                season=2026,
                week=9,
                season_type="regular",
                start_time=KICKOFF,
                home_id=1,
                away_id=2,
            )
        )


@pytest.mark.db
def test_publish_dedupes_and_snapshots_are_immutable(sessions) -> None:
    seed(sessions)
    monday, tuesday = KICKOFF - timedelta(days=5), KICKOFF - timedelta(days=4)

    first = publish_board(sessions, [board_game(56.0)], monday, FakeArtifact())
    again = publish_board(sessions, [board_game(56.0)], tuesday, FakeArtifact())
    moved = publish_board(sessions, [board_game(52.0)], tuesday, FakeArtifact())

    assert (first.published, first.picks) == (1, 1)  # over 45.5 at +10.5 points: a pick
    assert (again.published, again.unchanged, again.run_id) == (0, 1, None)
    assert moved.published == 1
    with sessions() as s:
        assert s.scalar(select(func.count()).select_from(Prediction)) == 2
    with pytest.raises(DBAPIError, match="immutable"), sessions.begin() as s:
        s.execute(update(Prediction).values(total=1.0))


@pytest.mark.db
def test_only_the_locked_snapshot_is_graded(sessions) -> None:
    seed(sessions)
    publish_board(sessions, [board_game(56.0)], KICKOFF - timedelta(days=5), FakeArtifact())
    publish_board(sessions, [board_game(58.0)], KICKOFF - timedelta(days=1), FakeArtifact())
    publish_board(sessions, [board_game(60.0)], KICKOFF + timedelta(minutes=5), FakeArtifact())
    with sessions.begin() as s:
        s.execute(
            update(Game).where(Game.id == 10).values(completed=True, home_points=30, away_points=24)
        )
        s.add(
            MarketLine(
                game_id=10,
                provider="DraftKings",
                spread=-3.5,
                total=47.0,
                fetched_at=KICKOFF,
                is_closing=True,
            )
        )

    result = grade_picks(sessions, KICKOFF + timedelta(days=1))

    assert (result.graded, result.wins) == (1, 1)  # one official pick: over 45.5, 54 scored
    with sessions() as s:
        graded = s.execute(select(Pick).where(Pick.result.is_not(None))).scalars().all()
        assert len(graded) == 1 and graded[0].closing_line == 47.0
        assert graded[0].units_won == pytest.approx(100 / 110)
    assert grade_picks(sessions, KICKOFF + timedelta(days=2)).graded == 0  # idempotent
