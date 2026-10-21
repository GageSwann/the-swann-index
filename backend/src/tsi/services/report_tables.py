"""The backtest report tables saved with each `tsi backtest run` (and written as CSV by
`tsi backtest export`). Pure transforms of a Book backtest; no I/O."""

from tsi.services import report_book as book_report
from tsi.services import report_export as report
from tsi.services.book_backtest import BookBacktest
from tsi.services.report_export import Table


def report_tables(book: BookBacktest) -> dict[str, Table]:
    result = book.model
    return {
        "by_season": report.by_season(result),
        "periods": report.periods(result),
        "calibration": report.calibration(result),
        "ats": report.ats(result),
        "totals_accuracy": book_report.totals_accuracy(result),
        "book_record": book_report.book_record(book),
        "book_calibration": book_report.book_calibration(result),
        "book_units": book_units(book),
    }


def book_units(book: BookBacktest) -> Table:
    """Cumulative Book units (flat and ¼ Kelly) after each game day, all seasons with openers."""
    flat = kelly = 0.0
    by_day: dict[str, dict] = {}
    for b in sorted(book.bets, key=lambda b: (b.kickoff is None, b.kickoff)):
        flat += b.units
        kelly += b.kelly_units
        if b.kickoff is not None:
            day = b.kickoff.date().isoformat()
            by_day[day] = {
                "date": day,
                "season": b.season,
                "units": round(flat, 2),
                "kelly_units": round(kelly, 2),
            }
    return list(by_day.values())
