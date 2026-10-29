"""`tsi run`: ingest -> rate -> grade -> publish, as of now (the nightly job runs this)."""

from datetime import UTC, datetime

import typer

from tsi.cli.runtime import db_runtime, ingest_runtime
from tsi.model.artifact import load_artifact
from tsi.services.run import RunResult, run_pipeline


def run(
    week: int | None = typer.Option(
        None, help="Publish only this week's games (default: next 8 days)."
    ),
    postseason: bool = typer.Option(False, help="With --week: a postseason week."),
    ingest: bool = typer.Option(True, help="Refresh from CFBD first (~4 calls)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Compute everything; save nothing."),
) -> None:
    """The full live pipeline. Exits 1 if ingest failed (later steps still ran on stored data)."""
    now = datetime.now(UTC)
    artifact = load_artifact()
    selected = None if week is None else ("postseason" if postseason else "regular", week)
    if ingest:
        with ingest_runtime() as (client, sessions):
            result = run_pipeline(sessions, now, artifact, client, selected, dry_run)
    else:
        with db_runtime() as sessions:
            result = run_pipeline(sessions, now, artifact, None, selected, dry_run)
    _report(result, now, artifact.version)
    if not result.ok:
        raise typer.Exit(1)


def _report(r: RunResult, now: datetime, version: str) -> None:
    typer.echo(f"tsi run {now:%Y-%m-%d %H:%M} UTC ({version})")
    if r.ingest_error:
        typer.secho(f"  ingest  FAILED: {r.ingest_error} (continued on stored data)", fg="red")
    elif r.ingest:
        typer.echo(f"  ingest  {r.ingest.summary()}")
    else:
        typer.echo("  ingest  skipped")
    top = r.ratings.rankings.teams[0] if r.ratings.rankings.teams else None
    leader = r.ratings.rankings.names[top.team_id] if top else "-"
    saved = f" -> model_runs.id={r.ratings_run_id}" if r.ratings_run_id else ""
    typer.echo(f"  rate    {len(r.ratings.predictive)} FBS teams, #1 {leader}{saved}")
    most = r.sim.teams[0] if r.sim and r.sim.teams else None
    if r.sim_error:
        typer.secho(f"  sim     FAILED: {r.sim_error} (everything else continued)", fg="red")
    elif r.sim and most:
        name = r.sim.names.get(most.team_id, "-")
        typer.echo(
            f"  sim     {r.sim.sims:,} seasons, most projected wins {name} {most.expected_wins:.1f}"
        )
    if r.grade:
        g = r.grade
        typer.echo(
            f"  grade   {g.graded} picks {g.wins}-{g.losses}-{g.pushes}, {g.units:+.2f} units"
        )
    picks = sum(len(b.picks) for b in r.board.games)
    typer.echo(f"  board   {len(r.board.games)} games, {picks} TSI Plays")
    if r.publish:
        p = r.publish
        typer.echo(
            f"  publish {p.published} new snapshots ({p.unchanged} unchanged), {p.picks} picks"
        )
    if r.publish is None and r.grade is None:
        typer.echo("  (dry run: nothing saved)")
