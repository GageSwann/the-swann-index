"""Adjust FBS-vs-FCS walk-forward margins and totals (decision #124) without leaking outcomes.

Same leave-one-season-out rule as the stacks and the rest adjustment: an FBS-vs-FCS
pick in a fitted season is scaled by factors fit on the other fitted seasons; every
other one by a fit on all of them. Other games are untouched.
"""

from collections.abc import Sequence
from dataclasses import replace

from tsi.backtest.walk_forward import Pick
from tsi.model.cross_division import (
    CrossDivision,
    CrossGame,
    fit_cross_division,
    is_cross_division,
)


def _cross(p: Pick) -> bool:
    return is_cross_division(p.game.home_div, p.game.away_div, p.game.season)


def apply_cross_division(
    picks: Sequence[Pick], seasons: tuple[int, int]
) -> tuple[list[Pick], CrossDivision]:
    """(scaled picks, the fit on every fitted pick: what production would use)."""
    fitted = [p for p in picks if _cross(p) and seasons[0] <= p.game.season <= seasons[1]]

    def fit(group: Sequence[Pick]) -> CrossDivision:
        return fit_cross_division(
            [
                CrossGame(
                    p.bucket,
                    p.predictive_margin,
                    p.game.margin,
                    p.predictive_total,
                    p.game.home_points + p.game.away_points,
                )
                for p in group
            ]
        )

    full = fit(fitted)
    held = {
        s: fit([p for p in fitted if p.game.season != s]) for s in {p.game.season for p in fitted}
    }

    def adjust(p: Pick) -> Pick:
        fit = held.get(p.game.season, full)
        return replace(
            p,
            predictive_margin=p.predictive_margin * fit.scale(p.bucket),
            predictive_total=p.predictive_total + fit.total,
        )

    return [adjust(p) if _cross(p) else p for p in picks], full
