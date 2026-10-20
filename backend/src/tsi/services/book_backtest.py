"""Backtest the TSI Book on top of the model backtest (same walk-forward picks).

Shrink (a, k) comes from the model backtest's TRAIN fit, so validation seasons
and the current season are out-of-sample. Records per period and per season.
"""

from dataclasses import dataclass

from tsi.backtest.book_eval import BookRecord, GradedBet, simulate_book, summarize_book
from tsi.backtest.splits import TRAIN, VALIDATE
from tsi.book.edges import EdgeShrink
from tsi.book.picks import PickRules
from tsi.model.config import ModelConfig
from tsi.services.backtest import BacktestResult, run_backtest
from tsi.services.backtest_data import BacktestData


@dataclass(frozen=True)
class BookBacktest:
    shrink: EdgeShrink
    records: list[BookRecord]  # by period ("Train ...", "Validate ...", single seasons)
    bets: list[GradedBet]
    model: BacktestResult  # the model backtest the Book was built on


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

    records = summarize_book(f"Train {TRAIN[0]}-{TRAIN[1]}", period(*TRAIN))
    records += summarize_book(f"Validate {VALIDATE[0]}-{VALIDATE[1]}", period(*VALIDATE))
    for season in sorted({b.season for b in bets}):
        records += summarize_book(str(season), period(season, season))
    return BookBacktest(shrink, records, bets, result)
