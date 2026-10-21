"""`tsi model ...`: run and evaluate rating models."""

from datetime import UTC, datetime

import typer

from tsi.backtest.evaluate import Summary
from tsi.cli.runtime import db_runtime, ingest_runtime
from tsi.ingest.freshness import current_season
from tsi.model.artifact import ARTIFACT_PATH, save_artifact
from tsi.model.elo import EloParams
from tsi.services.compute_rankings import build_rankings
from tsi.services.elo_report import run_elo_report
from tsi.services.model_fit import fit_production_model
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


@app.command()
def rankings(
    season: int | None = typer.Option(None, "--season", help="Season (default: current)."),
    top: int = typer.Option(25, help="How many teams to show."),
    by: str = typer.Option("power", help="Order by 'power' or 'resume'."),
) -> None:
    """Current Power + Résumé rankings (this season's games only)."""
    now = datetime.now(UTC)
    year = season or current_season(now)
    with db_runtime() as sessions, sessions() as session:
        result = build_rankings(session, year, now)

    teams = sorted(result.teams, key=lambda t: t.rank_resume) if by == "resume" else result.teams
    typer.echo(
        f"TSI {year} rankings as of {now:%Y-%m-%d %H:%M} UTC | HFA {result.ratings.hfa:.1f} | "
        f"Résumé benchmark (#12 rating) {result.benchmark:+.1f}\n"
    )
    typer.echo(
        f"{'Pwr':>3} {'Res':>3}  {'Team':<22}{'Rec':>6}  {'Rating':>6} {'Off':>6} {'Def':>6}  "
        f"{'SOR':>6} {'SOS':>6}"
    )
    for t in teams[:top]:
        r = t.resume
        flag = "*" if t.provisional else " "
        typer.echo(
            f"{t.rank_power:>3} {t.rank_resume:>3}  {result.names[t.team_id][:21]:<22}"
            f"{f'{r.wins}-{r.losses}':>6}{flag} {t.rating:>+6.1f} {t.off:>+6.1f} "
            f"{t.defense:>+6.1f}  {r.sor:>6.3f} {r.sos:>+6.1f}"
        )
    typer.echo("\n* provisional (fewer than 4 games). SOR = chance a #12 team matches the record.")


@app.command()
def fit(
    through: int | None = typer.Option(None, "--through", help="Last completed season."),
) -> None:
    """Fit the production model on all completed seasons and save the artifact (commit it)."""
    last = through or current_season(datetime.now(UTC)) - 1
    with db_runtime() as sessions, sessions() as session:
        artifact = fit_production_model(session, last)
    save_artifact(artifact)
    typer.echo(
        f"Saved {artifact.version} fitted on {artifact.fitted_seasons[0]}-"
        f"{artifact.fitted_seasons[1]} to {ARTIFACT_PATH}\n"
        f"{artifact.distribution.describe()}\n"
        f"edge shrink k spread {artifact.edge_shrink.k_spread:.3f}, "
        f"k total {artifact.edge_shrink.k_total:.3f}\n"
        f"sigma season {artifact.sigma_season:.1f} | {artifact.elo.elo_per_point:.1f} Elo per point"
    )
