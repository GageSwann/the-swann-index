"""`tsi model ...`: run and evaluate rating models."""

from datetime import UTC, datetime

import typer

from tsi.backtest.evaluate import Summary
from tsi.cli.runtime import db_runtime
from tsi.ingest.freshness import current_season
from tsi.model.elo import EloParams
from tsi.model.ratings.fit import RatingParams
from tsi.services.elo_report import run_elo_report
from tsi.services.ratings_report import run_ratings_report

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


@app.command()
def ratings(
    through: int | None = typer.Option(None, "--through", help="Last season (default: current)."),
    lam: float = typer.Option(RatingParams.lam, help="Ridge penalty (shrinkage toward average)."),
    ppd_weight: float = typer.Option(RatingParams.ppd_weight, help="Share of PPD vs. EPA."),
) -> None:
    """Walk-forward `season` ratings (this season only) vs. Elo and Vegas, FBS-vs-FBS."""
    last = through or current_season(datetime.now(UTC))
    params = RatingParams(lam=lam, ppd_weight=ppd_weight)
    with db_runtime() as sessions, sessions() as session:
        report = run_ratings_report(session, last, params)

    typer.echo(
        f"TSI season ratings: lam={params.lam:g} PPD weight={params.ppd_weight:g} | "
        f"win-prob sigma {report.sigma:.1f} pts (fit on train)\n"
    )
    typer.echo(
        f"{'':<24}{'games':>6}  {'TSI':>5} {'Elo':>5} {'Vegas':>5}  "
        f"{'TSI%':>5} {'Elo%':>5} {'Veg%':>5}  {'Brier':>5}"
    )
    for r in report.rows:
        t, e = r.tsi, r.elo
        bold = not t.label[:1].isdigit()
        typer.secho(
            f"{t.label:<24}{t.games:>6}  {t.mae:>5.2f} {e.mae:>5.2f} {t.market_mae:>5.2f}  "
            f"{100 * t.su_accuracy:>5.1f} {100 * e.su_accuracy:>5.1f} "
            f"{100 * t.market_su_accuracy:>5.1f}  {t.brier:>5.3f}",
            bold=bold,
        )
