"""Doc 05 §8 checks: are TSI's cover and over probabilities at the closing line honest?

For each game with a closing line, TSI's probability that the home side covers
(or the game goes over) comes from the score distribution; bins are on the side
TSI favors. Pushes are left out. Market lines are only the evaluation point here.
"""

from collections.abc import Mapping, Sequence

from tsi.backtest.calibration import CalibrationBin, calibration_table
from tsi.backtest.walk_forward import Pick
from tsi.model.distribution import DistributionParams

LINE_EDGES = (0.5, 0.55, 0.6, 0.65, 0.7, 1.0)  # cover/over probabilities sit near 50%


def cover_calibration(
    picks: Sequence[Pick], params: DistributionParams, spreads: Mapping[int, float]
) -> list[CalibrationBin]:
    probs, outcomes = [], []
    for p in picks:
        if p.game.id not in spreads:
            continue
        line = -spreads[p.game.id]  # home covers when margin > -spread
        if p.game.margin == line:
            continue
        dist = params.for_game(p.predictive_margin, p.predictive_total)
        probs.append(dist.p_margin_over(line))
        outcomes.append(1.0 if p.game.margin > line else 0.0)
    return calibration_table(probs, outcomes, LINE_EDGES)


def over_calibration(
    picks: Sequence[Pick], params: DistributionParams, totals: Mapping[int, float]
) -> list[CalibrationBin]:
    probs, outcomes = [], []
    for p in picks:
        if p.game.id not in totals:
            continue
        line, actual = totals[p.game.id], p.game.home_points + p.game.away_points
        if actual == line:
            continue
        dist = params.for_game(p.predictive_margin, p.predictive_total)
        probs.append(dist.p_total_over(line))
        outcomes.append(1.0 if actual > line else 0.0)
    return calibration_table(probs, outcomes, LINE_EDGES)
