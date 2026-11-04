from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from tsi.model.adjust import GameAdjustment, adjust_distribution, game_adjustment
from tsi.model.distribution import DistributionParams

KICKOFF = datetime(2026, 11, 7, 20, tzinfo=UTC)
PARAMS = DistributionParams(15.4, 16.4, 0.12, 0.0075)


@dataclass(frozen=True)
class Adj:
    id: int
    team_id: int
    off_points: float
    def_points: float
    starts_at: datetime = KICKOFF - timedelta(days=3)
    ends_at: datetime | None = None

    def covers(self, kickoff: datetime) -> bool:
        return self.starts_at <= kickoff and (self.ends_at is None or kickoff < self.ends_at)


def test_offense_moves_margin_and_total_defense_moves_margin_against_total() -> None:
    a = GameAdjustment((1,), home_off=-4.0, away_def=2.0)
    # home scores 4 fewer and 2 fewer again vs. the better away defense; away scores the same
    assert (a.margin_shift, a.total_shift) == (-6.0, -6.0)
    b = GameAdjustment((2,), home_def=3.0)  # home allows 3 fewer
    assert (b.margin_shift, b.total_shift) == (3.0, -3.0)


def test_sums_the_adjustments_covering_the_game_per_side() -> None:
    adjustments = [
        Adj(3, 1, -4.0, 0.0),
        Adj(1, 1, 0.0, -1.5),
        Adj(2, 2, 1.0, 0.0),
        Adj(4, 9, 5.0, 0.0),  # another team
        Adj(5, 2, 9.0, 0.0, ends_at=KICKOFF),  # ended at kickoff: doesn't cover it
        Adj(6, 1, 9.0, 0.0, starts_at=KICKOFF + timedelta(hours=1)),  # starts later
    ]

    got = game_adjustment(1, 2, KICKOFF, adjustments)

    assert got == GameAdjustment((1, 2, 3), home_off=-4.0, home_def=-1.5, away_off=1.0)
    assert game_adjustment(7, 8, KICKOFF, adjustments) is None


def test_adjusted_distribution_is_rebuilt_from_the_shifted_means() -> None:
    raw = PARAMS.for_game(4.0, 56.0)

    adj = adjust_distribution(raw, GameAdjustment((1,), home_off=-4.0), PARAMS)

    assert adj == PARAMS.for_game(0.0, 52.0)
    assert adj.home_points == pytest.approx(raw.home_points - 4)
    assert adj.away_points == pytest.approx(raw.away_points)
