"""Fill in walk-forward picks' stacked margin and total without leaking outcomes.

TRAIN seasons: leave-one-season-out (each season scored by weights learned on the
other train seasons). Everything else: weights learned on all of TRAIN.
"""

from collections.abc import Callable, Sequence
from dataclasses import replace

from tsi.backtest.splits import TRAIN
from tsi.backtest.walk_forward import Pick
from tsi.model.stack import StackModel, StackSample, fit_stack
from tsi.model.totals import TOTAL_FEATURES, TOTAL_UNPENALIZED


def margin_sample(p: Pick) -> StackSample:
    return StackSample(p.bucket, p.features, p.game.margin)


def total_sample(p: Pick) -> StackSample:
    return StackSample(p.bucket, p.total_features, p.game.home_points + p.game.away_points)


def fit_total_stack(picks: Sequence[Pick], lam: float) -> StackModel:
    return fit_stack([total_sample(p) for p in picks], lam, TOTAL_FEATURES, TOTAL_UNPENALIZED)


def fit_margin_stack(picks: Sequence[Pick], lam: float) -> StackModel:
    return fit_stack([margin_sample(p) for p in picks], lam)


def stacked_picks(picks: Sequence[Pick], lam: float, train: tuple[int, int] = TRAIN) -> list[Pick]:
    margin = _held_out(picks, lambda ps: fit_margin_stack(ps, lam), train)
    total = _held_out(picks, lambda ps: fit_total_stack(ps, lam), train)
    return [
        replace(
            p,
            predictive_margin=margin(p).predict(p.bucket, p.features),
            predictive_total=total(p).predict(p.bucket, p.total_features),
        )
        for p in picks
    ]


def _held_out(
    picks: Sequence[Pick],
    fit: Callable[[Sequence[Pick]], StackModel],
    train: tuple[int, int],
) -> Callable[[Pick], StackModel]:
    """Pick -> the stack that may score it (never one trained on its own season)."""
    fitted = [p for p in picks if train[0] <= p.game.season <= train[1]]
    full = fit(fitted)
    seasons = {p.game.season for p in fitted}
    held = {s: fit([p for p in fitted if p.game.season != s]) for s in seasons}
    return lambda p: held.get(p.game.season, full)
