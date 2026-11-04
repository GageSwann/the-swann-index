"""Adjusted games publish a raw and an adjusted row; the adjusted one is official (#104)."""

from datetime import timedelta

import pytest
from sqlalchemy import select, update

from tsi.book.edges import game_edges
from tsi.book.picks import choose_picks
from tsi.book.pricing import price_game
from tsi.db.models import Game, MarketLine, Pick, Prediction
from tsi.db.queries.predictions import ungraded_locked_picks
from tsi.db.queries.snapshots import snapshots_for_games
from tsi.model.adjust import GameAdjustment, adjust_distribution
from tsi.services.board import BoardGame
from tsi.services.grade import grade_picks
from tsi.services.predict import GameForecast
from tsi.services.publish import publish_board

from .test_publish_grade import KICKOFF, MARKET, PARAMS, FakeArtifact, board_game, seed

# Home offense -4 (QB out): margin 4 -> 0, total 56 -> 52.
QB_OUT = GameAdjustment(ids=(7,), home_off=-4.0)


def adjusted_game(total: float = 56.0) -> BoardGame:
    plain = board_game(total)
    raw = plain.forecast.distribution
    dist = adjust_distribution(raw, QB_OUT, PARAMS)
    edges = game_edges(dist, MARKET, FakeArtifact.edge_shrink)
    forecast = GameForecast(plain.forecast.game, 4, dist, QB_OUT, raw)
    return BoardGame(
        forecast, price_game(dist), MARKET, edges, choose_picks(edges), price_game(raw)
    )


@pytest.mark.db
def test_adjusted_publish_stores_both_rows_and_picks_on_the_adjusted_one(sessions) -> None:
    seed(sessions)
    monday, tuesday = KICKOFF - timedelta(days=5), KICKOFF - timedelta(days=4)

    first = publish_board(sessions, [adjusted_game()], monday, FakeArtifact())
    again = publish_board(sessions, [adjusted_game()], tuesday, FakeArtifact())

    assert (first.published, again.published, again.unchanged) == (1, 0, 1)
    with sessions() as s:
        rows = {p.variant: p for p in s.scalars(select(Prediction))}
        picks = s.scalars(select(Pick)).all()
    raw, adj = rows["raw"], rows["adjusted"]
    assert raw.published_at == adj.published_at == monday
    assert (raw.proj_home - raw.proj_away, raw.total) == pytest.approx((4.0, 56.0))
    assert (adj.proj_home - adj.proj_away, adj.total) == pytest.approx((0.0, 52.0))
    assert (raw.adjustment_ids, adj.adjustment_ids) == (None, [7])
    assert picks and {p.prediction_id for p in picks} == {adj.id}


@pytest.mark.db
def test_dropping_the_adjustment_publishes_a_new_raw_snapshot(sessions) -> None:
    seed(sessions)
    monday, tuesday = KICKOFF - timedelta(days=5), KICKOFF - timedelta(days=4)
    publish_board(sessions, [adjusted_game()], monday, FakeArtifact())

    expired = publish_board(sessions, [board_game(56.0)], tuesday, FakeArtifact())

    assert expired.published == 1  # same raw numbers, but the official forecast changed
    with sessions() as s:
        snaps = snapshots_for_games(s, [10])[10]
    assert [(s.variant, s.raw is not None) for s in snaps] == [("adjusted", True), ("raw", False)]
    assert snaps[0].adjustment_ids == [7] and snaps[0].raw.total == pytest.approx(56.0)


@pytest.mark.db
def test_the_locked_adjusted_snapshot_is_the_one_graded(sessions) -> None:
    seed(sessions)
    publish_board(sessions, [adjusted_game()], KICKOFF - timedelta(days=1), FakeArtifact())
    with sessions.begin() as s:
        s.execute(
            update(Game).where(Game.id == 10).values(completed=True, home_points=30, away_points=24)
        )
        s.add(MarketLine(game_id=10, provider="DraftKings", spread=-3.5, total=47.0,
                         fetched_at=KICKOFF, is_closing=True))  # fmt: skip
        adjusted_id = s.scalar(select(Prediction.id).where(Prediction.variant == "adjusted"))
        official = s.scalars(select(Pick.id).where(Pick.prediction_id == adjusted_id)).all()

    with sessions() as s:
        assert sorted(p.pick_id for p in ungraded_locked_picks(s)) == sorted(official)
    assert grade_picks(sessions, KICKOFF + timedelta(days=1)).graded == len(official)
