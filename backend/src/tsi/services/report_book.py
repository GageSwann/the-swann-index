"""Export the TSI Book backtest and totals accuracy as report tables."""

from tsi.services.backtest_result import BacktestResult
from tsi.services.book_backtest import BookBacktest
from tsi.services.report_export import PERIOD_LABELS, Table, bins_table

BOOK_PERIODS = {"Train": "Train 2021–22", "Validate": "Validate 2023–25"}  # openers: 2021+


def book_calibration(result: BacktestResult) -> Table:
    """The Book's shrunk P(home covers) / P(over) at the opener, validation seasons."""
    return [
        {"market": market, **row}
        for market, bins in (("spread", result.lines.cover), ("total", result.lines.over))
        for row in bins_table(bins)
    ]


def book_record(book: BookBacktest) -> Table:
    """Book record by period/season, market and star tier (tier 0 = all tiers)."""
    return [
        {
            "period": BOOK_PERIODS.get(r.label.split(" ")[0], r.label),
            "market": r.market,
            "tier": r.tier,
            "bets": r.bets,
            "wins": r.wins,
            "losses": r.losses,
            "pushes": r.pushes,
            "win_rate": round(r.win_rate, 4),
            "units": round(r.units, 2),
            "roi": round(r.roi, 4),
            "kelly_units": round(r.kelly_units, 2),
            "clv": None if r.clv is None else round(r.clv, 3),
            "beat_close": None if r.beat_close is None else round(r.beat_close, 4),
        }
        for r in book.records
    ]


def book_bets(book: BookBacktest) -> Table:
    """Every simulated Book bet, in kickoff order (for the cumulative-units chart)."""
    bets = sorted(book.bets, key=lambda b: (b.kickoff is None, b.kickoff))
    return [
        {
            "date": b.kickoff.date().isoformat() if b.kickoff else "",
            "season": b.season,
            "market": b.market,
            "side": b.side,
            "tier": b.tier,
            "result": b.result,
            "units": round(b.units, 4),
            "kelly_units": round(b.kelly_units, 4),
            "clv": None if b.clv is None else round(b.clv, 2),
        }
        for b in bets
    ]


def totals_accuracy(result: BacktestResult) -> Table:
    return [
        {
            "period": PERIOD_LABELS.get(t.label.split(" ")[0], t.label),
            "games": t.games,
            "tsi_mae": round(t.mae, 3),
            "vegas_mae": round(t.market_mae, 3),
            "bias": round(t.bias, 3),
            "ou_vs_close": round(t.ou_accuracy, 4),
        }
        for t in result.totals
    ]
