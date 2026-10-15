"""`tsi model ...`: run and evaluate rating models."""

from datetime import UTC, datetime

import typer

from tsi.backtest.evaluate import Summary
from tsi.cli.runtime import db_runtime, ingest_runtime
from tsi.ingest.freshness import current_season
from tsi.model.elo import EloParams
from tsi.services.elo_report import run_elo_report
from tsi.services.sp_check import compare_with_sp

app = typer.Typer(help="Run and evaluate rating models.", no_args_is_help=True)

HEADER = f"{'':<20}{'games':>6}  {'MAE':>5} {'Vegas':>5}  {'SU%':>5} {'Vegas':>5}  {'Brier':>6}"


@app.command()
def elo(
    through: int | None = typer.Option(None, "--through", help="Last season (default: current)."),
    k: float = typer.Option(EloParams.k, help="Update speed (K factor)."),
    hfa: float = typer.Option(EloParams.hfa, help="Home-field advantage in Elo points."),
    carryover: float = typer.Option(EloParams.carryover, help="Share kept between seasons."),
) -> None:
    """Elo baseline vs. the closing line on FBS-vs-FBS games (2014 = warm-up)."""
    last = through or current_season(datetime.now(UTC))
    params = EloParams(k=k, hfa=hfa, carryover=carryover)
    with db_runtime() as sessions, sessions() as session:
        report = run_elo_report(session, last, params)

    p = report.params
    typer.echo(
        f"Elo K={p.k:g} HFA={p.hfa:g} carryover={p.carryover:.2f} | "
        f"{p.elo_per_point:.1f} Elo = 1 point (fit on train seasons)\n"
    )
    typer.echo(HEADER)
    for row in report.seasons:
        typer.echo(_row(row))
    typer.echo("")
    for row in report.periods:
        typer.secho(_row(row), bold=True)


def _row(s: Summary) -> str:
    return (
        f"{s.label:<20}{s.games:>6}  {s.mae:>5.2f} {s.market_mae:>5.2f}  "
        f"{100 * s.su_accuracy:>5.1f} {100 * s.market_su_accuracy:>5.1f}  {s.brier:>6.3f}"
    )


@app.command("compare-sp")
def compare_sp(
    first: int = typer.Option(2015, help="First season."),
    last: int = typer.Option(2025, help="Last finished season."),
) -> None:
    """Sanity check: TSI final ratings vs. SP+ final ratings (~1 CFBD call/season, cached)."""
    with ingest_runtime() as (client, sessions), sessions() as session:
        results = compare_with_sp(client, session, range(first, last + 1))

    typer.echo(
        f"{'season':>6} {'teams':>5} {'pearson':>8} {'spearman':>9}   "
        "biggest rank gaps (TSI vs SP+)"
    )
    for r in results:
        a = r.agreement
        gaps = ", ".join(f"{r.names[t]} {o:+.1f}/{s:+.1f}" for t, o, s in a.biggest_gaps[:3])
        typer.echo(f"{r.season:>6} {a.teams:>5} {a.pearson:>8.3f} {a.spearman:>9.3f}   {gaps}")
    mean_p = sum(r.agreement.pearson for r in results) / len(results)
    mean_s = sum(r.agreement.spearman for r in results) / len(results)
    typer.secho(f"{'mean':>6} {'':>5} {mean_p:>8.3f} {mean_s:>9.3f}", bold=True)
