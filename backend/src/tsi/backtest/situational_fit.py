"""Add the rest/bye/short-week adjustment (decision #120) to stacked walk-forward picks.

Same leave-one-season-out rule as the stacks: a pick in a fitted season is adjusted by
coefficients fit on the other fitted seasons; every other pick by a fit on all of them.
Residuals are actual margin minus the stacked prediction.
"""

from collections.abc import Callable, Sequence
from dataclasses import replace

from tsi.backtest.walk_forward import Pick
from tsi.model.situational import Situational, fit_situational


def apply_situational(
    picks: Sequence[Pick],
    seasons: tuple[int, int],
    fit_on: Callable[[Pick], bool] = lambda p: True,
) -> tuple[list[Pick], Situational]:
    """(adjusted picks, the fit on every fitted pick: what production would use)."""
    fitted = [p for p in picks if fit_on(p) and seasons[0] <= p.game.season <= seasons[1]]

    def fit(group: Sequence[Pick]) -> Situational:
        return fit_situational([(p.situation, p.game.margin - p.predictive_margin) for p in group])

    full = fit(fitted)
    held = {
        s: fit([p for p in fitted if p.game.season != s]) for s in {p.game.season for p in fitted}
    }
    adjusted = [
        replace(
            p,
            predictive_margin=p.predictive_margin
            + held.get(p.game.season, full).shift(p.situation),
        )
        for p in picks
    ]
    return adjusted, full
