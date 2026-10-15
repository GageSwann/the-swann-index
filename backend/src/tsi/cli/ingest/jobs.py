"""Multi-step ingest jobs: `tsi ingest daily` and `tsi ingest season`."""

from datetime import UTC, datetime

import typer

from tsi.cli.ingest.app import REFRESH, SEASON, app
from tsi.cli.runtime import ingest_runtime
from tsi.services.daily import run_daily
from tsi.services.season import run_season


@app.command()
def daily() -> None:
    """Refresh the in-progress season (what the nightly GitHub Action runs)."""
    with ingest_runtime() as (client, sessions):
        result = run_daily(client, sessions, datetime.now(UTC))
    typer.echo(f"daily {result.summary()}")


@app.command()
def season(
    season: int = SEASON,
    through: int | None = typer.Option(
        None, "--through", help="Load every season from --season through this one."
    ),
    refresh: bool = REFRESH,
) -> None:
    """Everything for a season (or a range), in dependency order: ~9 CFBD calls each."""
    last = through or season
    if last < season:
        raise typer.BadParameter("--through must be >= --season")
    with ingest_runtime() as (client, sessions):
        for year in range(season, last + 1):
            typer.echo(f"season {run_season(client, sessions, year, refresh=refresh).summary()}")
