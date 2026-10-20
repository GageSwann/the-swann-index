"""Doc 05 §8 checks + the edge shrink fit (decision #52), against market lines.

The Book's probability that the home side covers (or the game goes over) is TSI's
distribution shrunk toward the line by k (book/edges.py). k is fit here on past
games at the line the Book bets (historically the median opener), then the
probabilities are checked in bins on the side TSI favors. Pushes are left out.
Market lines are only evaluation points and the edge scale, never model inputs.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from tsi.backtest.calibration import CalibrationBin, calibration_table
from tsi.backtest.walk_forward import Pick
from tsi.book.edges import EdgeShrink
from tsi.book.shrink_fit import fit_k
from tsi.model.distribution import DistributionParams
from tsi.model.distribution_fit import normal_cdf

LINE_EDGES = (0.5, 0.52, 0.54, 0.56, 0.58, 1.0)  # shrunk probabilities sit near 50%


@dataclass(frozen=True)
class LineSample:
    z: float  # (TSI mean - line mean) / sigma
    outcome: float  # 1 if home covered / game went over


def spread_samples(
    picks: Sequence[Pick], params: DistributionParams, spreads: Mapping[int, float | None]
) -> list[LineSample]:
    out = []
    for p in picks:
        spread = spreads.get(p.game.id)
        if spread is None or p.game.margin == -spread:
            continue
        dist = params.for_game(p.predictive_margin, p.predictive_total)
        z = (dist.margin + spread) / dist.sigma_margin
        out.append(LineSample(z, 1.0 if p.game.margin > -spread else 0.0))
    return out


def total_samples(
    picks: Sequence[Pick], params: DistributionParams, totals: Mapping[int, float | None]
) -> list[LineSample]:
    out = []
    for p in picks:
        line, actual = totals.get(p.game.id), p.game.home_points + p.game.away_points
        if line is None or actual == line:
            continue
        dist = params.for_game(p.predictive_margin, p.predictive_total)
        out.append(LineSample((dist.total - line) / dist.sigma_total, float(actual > line)))
    return out


def fit_edge_shrink(spreads: Sequence[LineSample], totals: Sequence[LineSample]) -> EdgeShrink:
    return EdgeShrink(
        k_spread=fit_k([s.z for s in spreads], [s.outcome for s in spreads]),
        k_total=fit_k([s.z for s in totals], [s.outcome for s in totals]),
    )


def line_calibration(samples: Sequence[LineSample], k: float) -> list[CalibrationBin]:
    probs = normal_cdf(k * np.array([s.z for s in samples], dtype=float))
    return calibration_table(list(probs), [s.outcome for s in samples], LINE_EDGES)


@dataclass(frozen=True)
class LineCheck:
    shrink: EdgeShrink  # fit on the train picks
    cover: list[CalibrationBin]  # shrunk P(home covers), validation picks
    over: list[CalibrationBin]  # shrunk P(over), validation picks


def line_check(
    train: Sequence[Pick],
    validate: Sequence[Pick],
    params: DistributionParams,
    spreads: Mapping[int, float | None],
    totals: Mapping[int, float | None],
) -> LineCheck:
    shrink = fit_edge_shrink(
        spread_samples(train, params, spreads), total_samples(train, params, totals)
    )
    return LineCheck(
        shrink,
        line_calibration(spread_samples(validate, params, spreads), shrink.k_spread),
        line_calibration(total_samples(validate, params, totals), shrink.k_total),
    )
