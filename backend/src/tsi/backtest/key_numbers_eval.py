"""Key numbers in the backtest (decision #118): fit the weights on TRAIN picks, then score
validation games with and without them (log loss of the actual margin and total) and
compare predicted with actual push rates at whole-number closing spreads."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import log

from tsi.backtest.walk_forward import Pick
from tsi.model.distribution import DistributionParams
from tsi.model.key_numbers import KeyNumbers
from tsi.model.key_numbers_fit import fit_key_numbers

KEY_SPREADS = (3, 7, 10, 14)


@dataclass(frozen=True)
class PushRate:
    spread: int | None  # |closing spread|; None = every other whole number
    games: int
    predicted: float
    actual: float


@dataclass(frozen=True)
class KeyNumberCheck:
    games: int  # validation games
    margin_log_loss: float  # with key numbers
    margin_log_loss_normal: float  # the smooth normal, discretized (ties included)
    total_log_loss: float
    total_log_loss_normal: float
    pushes: list[PushRate]  # at whole-number closing spreads, validation


def fit_on(picks: Sequence[Pick], params: DistributionParams) -> KeyNumbers:
    return fit_key_numbers(
        [(p.predictive_margin, params.sigma_margin, p.game.margin) for p in picks],
        [(p.predictive_total, _sigma_total(p, params), _total(p)) for p in picks],
    )


def check(
    keys: KeyNumbers,
    picks: Sequence[Pick],
    params: DistributionParams,
    closing: Mapping[int, float],
) -> KeyNumberCheck:
    plain = KeyNumbers.none()

    def margin_ll(k: KeyNumbers) -> float:
        return _mean(
            -log(max(k.margin_table(p.predictive_margin, params.sigma_margin).p_at(p.game.margin),
                     1e-12))
            for p in picks
        )  # fmt: skip

    def total_ll(k: KeyNumbers) -> float:
        return _mean(
            -log(max(k.total_table(p.predictive_total, _sigma_total(p, params)).p_at(_total(p)),
                     1e-12))
            for p in picks
        )  # fmt: skip

    pushes: dict[int | None, list[tuple[float, bool]]] = {}
    for p in picks:
        spread = closing.get(p.game.id)
        if spread is None or spread == 0 or not float(spread).is_integer():
            continue
        size = abs(int(spread))
        table = keys.margin_table(p.predictive_margin, params.sigma_margin)
        bucket = size if size in KEY_SPREADS else None
        pushes.setdefault(bucket, []).append((table.p_at(-int(spread)), p.game.margin == -spread))
    rates = [
        PushRate(b, len(v), _mean(x for x, _ in v), _mean(float(y) for _, y in v))
        for b in (*KEY_SPREADS, None)
        if (v := pushes.get(b))
    ]
    return KeyNumberCheck(
        len(picks), margin_ll(keys), margin_ll(plain), total_ll(keys), total_ll(plain), rates
    )


def _sigma_total(p: Pick, params: DistributionParams) -> float:
    return params.for_game(p.predictive_margin, p.predictive_total).sigma_total


def _total(p: Pick) -> int:
    return p.game.home_points + p.game.away_points


def _mean(values) -> float:
    xs = list(values)
    return sum(xs) / len(xs) if xs else float("nan")
