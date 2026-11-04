"""Backtest the TSI Book on top of the model backtest (same walk-forward picks).

Shrink (a, k) comes from the model backtest's TRAIN fit, so validation seasons
and the current season are out-of-sample. Records per period and per season.

FCS (decision #112): the same rules on games with an individually rated FCS team, which
the live Book doesn't pick (#108). Two shrinks: the FBS one (what turning FCS picks on
today would do) and one fit on the FCS train season(s) (does FCS need its own trust?).
"""

from collections.abc import Sequence
from dataclasses import dataclass

from tsi.backtest.book_eval import BookRecord, GradedBet, simulate_book, summarize_book
from tsi.backtest.market_calibration import fit_edge_shrink, spread_samples, total_samples
from tsi.backtest.splits import TRAIN, VALIDATE
from tsi.backtest.walk_forward import Pick
from tsi.book.edges import EdgeShrink
from tsi.book.picks import PickRules
from tsi.divisions import RATED_DIVISION
from tsi.model.config import ModelConfig
from tsi.services.backtest import run_backtest
from tsi.services.backtest_data import BacktestData
from tsi.services.backtest_result import BacktestResult


@dataclass(frozen=True)
class FcsBook:
    shrink: EdgeShrink
    label: str  # which shrink: "FBS shrink" or "FCS shrink"
    records: list[BookRecord]  # train / validate, all FCS games and FCS vs. FCS / FBS vs. FCS


@dataclass(frozen=True)
class BookBacktest:
    shrink: EdgeShrink
    records: list[BookRecord]  # by period ("Train ...", "Validate ...", single seasons)
    bets: list[GradedBet]
    model: BacktestResult  # the model backtest the Book was built on
    fcs: list[FcsBook]  # report only: FCS picks are off (#108, #112)


def run_book_backtest(
    data: BacktestData, config: ModelConfig | None = None, rules: PickRules | None = None
) -> BookBacktest:
    result = run_backtest(data, config)
    shrink = result.lines.shrink
    bets = simulate_book(
        result.picks,
        result.distribution,
        shrink,
        data.opening,
        data.closing,
        data.closing_totals,
        rules,
    )

    def period(first: int, last: int) -> list[GradedBet]:
        return [b for b in bets if first <= b.season <= last]

    def label(name: str, first: int, last: int) -> str:
        """Name the seasons that actually have bets (openers only exist from 2021)."""
        seasons = [b.season for b in period(first, last)] or [first, last]
        return f"{name} {min(seasons)}-{max(seasons)}"

    records = summarize_book(label("Train", *TRAIN), period(*TRAIN))
    records += summarize_book(label("Validate", *VALIDATE), period(*VALIDATE))
    for season in sorted({b.season for b in bets}):
        records += summarize_book(str(season), period(season, season))
    fcs = [
        _fcs_book(result, data, s, name, rules)
        for s, name in ((shrink, "FBS shrink"), (_fcs_shrink(result, data), "FCS shrink"))
    ]
    return BookBacktest(shrink, records, bets, result, fcs)


def _fcs_shrink(result: BacktestResult, data: BacktestData) -> EdgeShrink:
    """Trust in TSI vs. the opener, fit on FCS games in the train seasons only."""
    train = [p for p in result.fcs_picks if TRAIN[0] <= p.game.season <= TRAIN[1]]
    opening = data.opening
    return fit_edge_shrink(
        spread_samples(train, result.distribution, {g: o.spread for g, o in opening.items()}),
        total_samples(train, result.distribution, {g: o.total for g, o in opening.items()}),
    )


def _fcs_book(
    result: BacktestResult,
    data: BacktestData,
    shrink: EdgeShrink,
    name: str,
    rules: PickRules | None,
) -> FcsBook:
    def book(picks: Sequence[Pick]) -> list[GradedBet]:
        return simulate_book(
            picks, result.distribution, shrink, data.opening, data.closing, data.closing_totals,
            rules,
        )  # fmt: skip

    def fbs_involved(p: Pick) -> bool:
        return RATED_DIVISION in (p.game.home_div, p.game.away_div)

    records: list[BookRecord] = []
    for period, (first, last) in (("train", TRAIN), ("validate", VALIDATE)):
        picks = [p for p in result.fcs_picks if first <= p.game.season <= last]
        seasons = sorted({p.game.season for p in picks})
        if not seasons:
            continue
        span = f"{seasons[0]}" + (f"-{seasons[-1]}" if len(seasons) > 1 else "")
        records += summarize_book(f"All FCS, {period} {span}", book(picks))
        records += [
            r
            for r in summarize_book(
                f"FCS vs FCS, {period}", book([p for p in picks if not fbs_involved(p)])
            )
            if r.tier == 0
        ]
        records += [
            r
            for r in summarize_book(
                f"FBS vs FCS, {period}", book([p for p in picks if fbs_involved(p)])
            )
            if r.tier == 0
        ]
    return FcsBook(shrink, name, records)
