"""`tsi rebuild ...`: fill in days the nightly job never ran (roadmap 13.8, #152)."""

from datetime import UTC, datetime

import typer

from tsi.cli.runtime import db_runtime
from tsi.ingest.freshness import current_season
from tsi.model.artifact import load_artifact
from tsi.services.rebuild_run import DayResult, latest_run, rebuild_season, verify_run

app = typer.Typer(help="Rebuild missing days through the live code.", no_args_is_help=True)


@app.command()
def verify(
    run_id: int = typer.Argument(None, help="Run to replay (default: the newest nightly run)."),
) -> None:
    """Replay a stored nightly run and compare every rating and forecast (exit 1 if any differ)."""
    with db_runtime() as sessions, sessions() as session:
        artifact = load_artifact()
        run_id = run_id or latest_run(session, current_season(datetime.now(UTC)))
        if run_id is None:
            typer.echo("no nightly run to verify")
            raise typer.Exit(1)
        r = verify_run(session, run_id, artifact)
    typer.echo(
        f"run {r.run_id} at {r.run_at:%Y-%m-%d %H:%M} UTC: {r.ratings} ratings, "
        f"{r.rating_diffs} differ; {r.forecasts} published forecasts, {r.forecast_diffs} differ"
    )
    typer.echo("verify OK" if r.ok else "verify FAILED")
    if not r.ok:
        raise typer.Exit(1)


@app.command()
def season(
    dry_run: bool = typer.Option(False, help="Compute every day, store nothing."),
    sims: int = typer.Option(None, help="Simulated seasons on Sundays (default: the nightly's)."),
) -> None:
    """Rebuild every day of the current season that has no rating run or whose games have no
    forecast: rating runs, rebuilt forecasts, and on Sundays the sim and games of the week."""
    now = datetime.now(UTC)
    with db_runtime() as sessions:
        results = rebuild_season(
            sessions,
            current_season(now),
            now,
            load_artifact(),
            dry_run=dry_run,
            sims=sims,
            on_day=_print_day,
        )
    runs = sum(1 for r in results if r.stored and r.stored.run_id)
    games = sum(r.stored.forecasts for r in results if r.stored)
    typer.echo(
        f"{len(results)} days rebuilt"
        + ("" if dry_run else f": {runs} rating runs, {games} games given a rebuilt forecast")
        + (" (dry run: nothing stored)" if dry_run else "")
    )


def _print_day(r: DayResult) -> None:
    what = "run + forecasts" if r.store_run else "forecasts only"
    stored = ""
    if r.stored:
        stored = f" -> run {r.stored.run_id or '-'}, {r.stored.forecasts} forecasts"
        if r.stored.sim:
            stored += ", sim"
        if r.stored.games_of_week:
            stored += f", {r.stored.games_of_week} games of the week"
    typer.echo(f"{r.day}  {what:<16} {r.teams:>3} FBS ranked, {r.final_games:>3} games{stored}")
