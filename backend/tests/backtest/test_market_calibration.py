from datetime import UTC, datetime

from tsi.backtest.market_calibration import cover_calibration, over_calibration
from tsi.backtest.walk_forward import Pick
from tsi.db.queries.results import GameResult
from tsi.model.distribution import DistributionParams

PARAMS = DistributionParams(15.0, 16.0, 0.0, 0.0)


def pick(gid: int, home: int, away: int, margin: float, total: float) -> Pick:
    kickoff = datetime(2024, 9, 7, tzinfo=UTC)
    g = GameResult(gid, 2024, kickoff, 1, 2, "fbs", "fbs", False, home, away)
    return Pick(g, margin, margin, total, True, 4, (), ())


def test_cover_probability_uses_the_home_view_spread() -> None:
    # TSI: home by 10; line home -3 -> TSI likes home to cover. Home won by 7: covered.
    picks = [pick(1, 27, 20, 10.0, 47.0), pick(2, 20, 17, 10.0, 37.0)]  # game 2: push at -3

    bins = cover_calibration(picks, PARAMS, {1: -3.0, 2: -3.0})

    assert sum(b.games for b in bins) == 1
    assert bins[0].predicted > 0.5 and bins[0].observed == 1.0


def test_over_probability_and_missing_lines() -> None:
    picks = [pick(1, 30, 30, 0.0, 50.0), pick(2, 10, 10, 0.0, 50.0)]

    bins = over_calibration(picks, PARAMS, {1: 55.0})  # game 2 has no total

    assert sum(b.games for b in bins) == 1
    assert bins[0].observed == 0.0  # TSI leaned under (50 < 55); 60 went over
