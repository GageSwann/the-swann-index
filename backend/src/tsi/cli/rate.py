"""`tsi rate`: compute today's live ratings and store them (the nightly job runs this)."""

from datetime import UTC, datetime

import typer

from tsi.cli.runtime import db_runtime
from tsi.model.artifact import load_artifact
from tsi.services.rate import compute_live_ratings
from tsi.services.rate_store import save_live_ratings


def rate(
    dry_run: bool = typer.Option(False, "--dry-run", help="Compute and print; don't save."),
    top: int = typer.Option(10, help="How many teams to print."),
) -> None:
    """Refit today's `season` + `predictive` ratings and rankings; save as a live model run."""
    now = datetime.now(UTC)
    artifact = load_artifact()
    with db_runtime() as sessions:
        with sessions() as session:
            live = compute_live_ratings(session, now, artifact)
        run_id = None if dry_run else save_live_ratings(sessions, live, artifact)

    names = live.rankings.names
    pred_rank = {
        t.team_id: i + 1
        for i, t in enumerate(sorted(live.predictive, key=lambda t: -t.rating.rating))
    }
    pred = {t.team_id: t.rating.rating for t in live.predictive}
    typer.echo(f"{live.season} as of {now:%Y-%m-%d %H:%M} UTC ({artifact.version})")
    typer.echo(f"{'Pwr':>3} {'Res':>3} {'Pred':>4}  {'Team':<22}{'Season':>7}{'Predictive':>11}")
    for t in live.rankings.teams[:top]:
        typer.echo(
            f"{t.rank_power:>3} {t.rank_resume:>3} {pred_rank.get(t.team_id, 0):>4}  "
            f"{names[t.team_id][:21]:<22}{t.rating:>+7.1f}{pred.get(t.team_id, 0.0):>+11.1f}"
        )
    if run_id is not None:
        typer.echo(
            f"\nSaved as model_runs.id={run_id} (kind=live), {2 * len(live.predictive)} rows"
        )
