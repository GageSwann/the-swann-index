"""`tsi backtest book`: the TSI Book's historical record at the opening line, by ★ tier."""

from datetime import UTC, datetime

import typer

from tsi.backtest.book_eval import BookRecord
from tsi.book.edges import BREAK_EVEN
from tsi.cli.runtime import db_runtime
from tsi.ingest.freshness import current_season
from tsi.services.backtest_data import load_backtest_data
from tsi.services.book_backtest import run_book_backtest


def book(
    through: int | None = typer.Option(None, "--through", help="Last season (default: current)."),
    seasons: bool = typer.Option(False, "--seasons", help="Also print each season."),
) -> None:
    """Picks the Book would have made (2021+, openers), graded: W-L-P, ROI, Kelly, CLV."""
    last = through or current_season(datetime.now(UTC))
    with db_runtime() as sessions, sessions() as session:
        data = load_backtest_data(session, last)
    result = run_book_backtest(data)

    k = result.shrink
    typer.echo(
        f"Shrink from train: k spread {k.k_spread:.3f}, "
        f"k total {k.k_total:.3f}. Bets at the median opener, -110 "
        f"(break-even {100 * BREAK_EVEN:.1f}%); CLV vs. closing consensus.\n"
    )
    typer.echo(
        f"{'':<20}{'market':<7}{'tier':<5}{'W-L-P':>12}{'win%':>7}{'units':>8}{'ROI':>9}"
        f"{'kelly':>8}{'CLV':>7}{'beat':>6}"
    )
    for r in result.records:
        if not seasons and r.label[:1].isdigit():
            continue
        typer.secho(_row(r), bold=r.tier == 0)


def _row(r: BookRecord) -> str:
    tier = "all" if r.tier == 0 else "*" * r.tier
    clv = "" if r.clv is None else f"{r.clv:+.2f}"
    beat = "" if r.beat_close is None else f"{100 * r.beat_close:.0f}%"
    return (
        f"{r.label:<20}{r.market:<7}{tier:<5}{f'{r.wins}-{r.losses}-{r.pushes}':>12}"
        f"{100 * r.win_rate:>6.1f}%{r.units:>+8.1f}{100 * r.roi:>+8.1f}%"
        f"{r.kelly_units:>+8.1f}{clv:>7}{beat:>6}"
    )
