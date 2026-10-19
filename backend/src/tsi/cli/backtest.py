"""`tsi backtest run`: walk-forward backtest of the full model, saved to model_runs."""

from datetime import UTC, datetime
from pathlib import Path

import typer

from tsi.backtest.ats import BREAK_EVEN
from tsi.backtest.calibration import TOLERANCE
from tsi.cli.runtime import db_runtime, ingest_runtime
from tsi.ingest.freshness import current_season
from tsi.model.artifact import load_artifact
from tsi.model.config import ModelConfig
from tsi.model.ratings.fit import RatingParams
from tsi.model.stack import DEFAULT_LAM
from tsi.services import report_export as report
from tsi.services.backtest import BacktestResult, run_backtest
from tsi.services.backtest_data import load_backtest_data
from tsi.services.backtest_store import save_backtest_run

app = typer.Typer(help="Walk-forward backtests.", no_args_is_help=True)
OUT_DIR = typer.Option(..., "--out-dir", help="Folder for the report CSVs.")


@app.command()
def run(
    through: int | None = typer.Option(None, "--through", help="Last season (default: current)."),
    lam: float = typer.Option(RatingParams.lam, help="Ridge penalty."),
    stack_lam: float = typer.Option(DEFAULT_LAM, help="Ridge penalty on the predictive stack."),
    save: bool = typer.Option(True, help="Save the run to model_runs (kind='backtest')."),
) -> None:
    """TSI `season` + `predictive` vs. Elo and Vegas, plus calibration and ATS (validation)."""
    last = through or current_season(datetime.now(UTC))
    config = ModelConfig(RatingParams(lam=lam), stack_lam)
    with db_runtime() as sessions:
        with sessions() as session:
            data = load_backtest_data(session, last)
        result = run_backtest(data, config)
        run_id = save_backtest_run(sessions, result, last) if save else None

    _print_summary(result)
    _print_calibration(result)
    _print_ats(result)
    if run_id is not None:
        typer.echo(f"\nSaved as model_runs.id={run_id} (kind=backtest)")


def _print_summary(result: BacktestResult) -> None:
    c = result.config
    typer.echo(
        f"TSI {c.to_dict()['version']}: lam={c.rating.lam:g} | season blend PPD "
        f"{c.rating.ppd_weight:g} + success {c.rating.success_weight:g}, HFA {c.rating.hfa:g} | "
        f"stack lam {c.stack_lam:g} | sigma {result.sigma:.1f}\n"
        "MAE: Season = this season only (rankings), Pred = stacked prediction\n"
    )
    typer.echo(
        f"{'':<24}{'games':>6}  {'Season':>6} {'Pred':>5} {'Elo':>5} {'Vegas':>5}  "
        f"{'Pred%':>5} {'Elo%':>5} {'Veg%':>5}  {'Brier':>5}"
    )
    for r in result.rows:
        s, p, e = r.season, r.predictive, r.elo
        typer.secho(
            f"{s.label:<24}{s.games:>6}  {s.mae:>6.2f} {p.mae:>5.2f} {e.mae:>5.2f} "
            f"{s.market_mae:>5.2f}  {100 * p.su_accuracy:>5.1f} {100 * e.su_accuracy:>5.1f} "
            f"{100 * p.market_su_accuracy:>5.1f}  {p.brier:>5.3f}",
            bold=not s.label[:1].isdigit(),
        )


def _print_calibration(result: BacktestResult) -> None:
    typer.echo(
        f"\nCalibration, validation (favorite's win prob; target ±{100 * TOLERANCE:.0f} pts)"
    )
    for b in result.calibration:
        typer.secho(
            f"  {100 * b.low:3.0f}-{100 * b.high:3.0f}%  games {b.games:>4}  "
            f"predicted {100 * b.predicted:5.1f}%  observed {100 * b.observed:5.1f}%  "
            f"({100 * b.error:+.1f})",
            fg="green" if b.within_tolerance else "yellow",
        )


def _print_ats(result: BacktestResult) -> None:
    typer.echo(f"\nAgainst the closing spread, validation (break-even {100 * BREAK_EVEN:.1f}%)")
    for a in result.ats:
        typer.echo(
            f"  edge >= {a.min_edge:>3.0f} pts: {a.wins}-{a.losses}-{a.pushes}  "
            f"({100 * a.win_rate:.1f}% of {a.bets} bets)"
        )


@app.command()
def export(
    out_dir: Path = OUT_DIR,
    through: int | None = typer.Option(None, "--through", help="Last season (default: current)."),
) -> None:
    """Write the Phase 2 report tables (backtest, calibration, ATS, SP+, stack weights) as CSV."""
    last = through or current_season(datetime.now(UTC))
    with ingest_runtime() as (client, sessions), sessions() as session:
        result = run_backtest(load_backtest_data(session, last))
        sp = report.sp_agreement(client, session, 2015, last - 1)
    tables = {
        "by_season": report.by_season(result),
        "periods": report.periods(result),
        "calibration": report.calibration(result),
        "ats": report.ats(result),
        "sp_agreement": sp,
        "stack_weights": report.stack_weights(load_artifact()),
    }
    for name, rows in tables.items():
        report.write_csv(rows, out_dir / f"{name}.csv")
        typer.echo(f"{name}.csv: {len(rows)} rows")
