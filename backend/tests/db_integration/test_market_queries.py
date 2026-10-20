"""Market line queries against a real (throwaway) schema."""

from datetime import UTC, datetime, timedelta

import pytest

from tsi.db.models import Game, MarketLine, Team
from tsi.db.queries.market import line_snapshots, opening_lines

KICKOFF = datetime(2026, 10, 24, 19, 30, tzinfo=UTC)


def seed(session) -> None:
    session.add_all(
        [Team(id=1, school="Home", slug="home"), Team(id=2, school="Away", slug="away")]
    )
    session.flush()
    session.add(
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
    session.flush()

    def line(provider, spread, days_before, closing=False, spread_open=None, total_open=None):
        session.add(
            MarketLine(
                game_id=10,
                provider=provider,
                spread=spread,
                total=50.5,
                home_ml=-150,
                away_ml=130,
                fetched_at=KICKOFF - timedelta(days=days_before),
                is_closing=closing,
                spread_open=spread_open,
                total_open=total_open,
            )
        )

    line("DraftKings", -3.0, 5)
    line("DraftKings", -4.0, 2)
    line("DraftKings", -4.5, 0, closing=True, spread_open=-2.5, total_open=48.0)
    line("Bovada", -3.5, 4)
    line("Bovada", -4.5, 0, closing=True, spread_open=-3.5, total_open=49.0)
    line("ESPN Bet", -5.0, 0, closing=True, spread_open=-12.0, total_open=50.0)  # odd opener
    line("consensus", -9.0, 3)  # aggregator: ignored


@pytest.mark.db
def test_line_snapshots_take_each_books_latest_line_as_of(sessions) -> None:
    with sessions.begin() as s:
        seed(s)
    with sessions() as s:
        snaps = line_snapshots(s, [10], KICKOFF - timedelta(days=3))

    assert {(x.provider, x.spread) for x in snaps} == {("DraftKings", -3.0), ("Bovada", -3.5)}


@pytest.mark.db
def test_opening_lines_are_medians_across_books(sessions) -> None:
    with sessions.begin() as s:
        seed(s)
    with sessions() as s:
        opening = opening_lines(s, 2026)

    assert opening[10].spread == -3.5  # median of -2.5, -3.5, -12.0
    assert opening[10].total == 49.0
