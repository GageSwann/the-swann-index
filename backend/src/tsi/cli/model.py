"""`tsi model ...`: run and evaluate rating models."""

from datetime import UTC, datetime

import typer

from tsi.backtest.evaluate import Summary
from tsi.cli.runtime import db_runtime
from tsi.ingest.freshness import current_season
from tsi.model.blend import BlendParams
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
    prior_games: float = typer.Option(BlendParams.prior_games, help="Prior's weight in games."),
    cutoff_games: float = typer.Option(BlendParams.cutoff_games, help="Games until prior = 0."),
) -> None:
    """Walk-forward TSI `season` + `predictive` ratings vs. Elo and Vegas, FBS-vs-FBS."""
    last = through or current_season(datetime.now(UTC))
    rating_params = RatingParams(lam=lam, ppd_weight=ppd_weight)
    blend_params = BlendParams(prior_games=prior_games, cutoff_games=cutoff_games)
    with db_runtime() as sessions, sessions() as session:
        report = run_ratings_report(session, last, rating_params, blend_params)

    typer.echo(
        f"TSI: lam={lam:g} PPD weight={ppd_weight:g} | prior worth {prior_games:g} games, "
        f"gone after {cutoff_games:g} | prior HFA {report.prior_hfa:.1f}\n"
        "MAE columns: Season = this season only (rankings), Pred = with prior (predictions)\n"
    )
    typer.echo(
        f"{'':<24}{'games':>6}  {'Season':>6} {'Pred':>5} {'Elo':>5} {'Vegas':>5}  "
        f"{'Pred%':>5} {'Elo%':>5} {'Veg%':>5}  {'Brier':>5}"
    )
    for r in report.rows:
        s, p, e = r.season, r.predictive, r.elo
        typer.secho(
            f"{s.label:<24}{s.games:>6}  {s.mae:>6.2f} {p.mae:>5.2f} {e.mae:>5.2f} "
            f"{s.market_mae:>5.2f}  {100 * p.su_accuracy:>5.1f} {100 * e.su_accuracy:>5.1f} "
            f"{100 * p.market_su_accuracy:>5.1f}  {p.brier:>5.3f}",
            bold=not s.label[:1].isdigit(),
        )
