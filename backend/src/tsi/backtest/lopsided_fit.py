"""Fit and apply the lopsided-game total bump on walk-forward picks (#132).

Mirrors `cross_division_fit`: seasons inside the fitted range get a fit that leaves
their own season out; later seasons get the fit on the whole range, which is what
production uses. Fit and applied only on games with an individually rated FCS team
(`lopsided.applies`), after the FBS-vs-FCS step; then every pick's total, of every game
kind, is floored so no underdog projects below `MIN_POINTS`.
"""

from collections.abc import Sequence
from dataclasses import replace

from tsi.backtest.walk_forward import Pick
from tsi.model.lopsided import NONE, Lopsided, TotalGame, applies, fit_lopsided, floored_total


def _applies(p: Pick) -> bool:
    return applies(p.game.home_div, p.game.away_div, p.game.season)


def apply_lopsided(picks: Sequence[Pick], seasons: tuple[int, int]) -> tuple[list[Pick], Lopsided]:
    """(bumped and floored picks, the fit on every fitted pick: what production would use)."""
    fitted = [p for p in picks if _applies(p) and seasons[0] <= p.game.season <= seasons[1]]

    def fit(group: Sequence[Pick]) -> Lopsided:
        return fit_lopsided(
            [
                TotalGame(
                    p.predictive_margin,
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
        lop = held.get(p.game.season, full) if _applies(p) else NONE
        bumped = lop.bump(p.predictive_margin, p.predictive_total)
        return replace(p, predictive_total=floored_total(p.predictive_margin, bumped))

    return [adjust(p) for p in picks], full
