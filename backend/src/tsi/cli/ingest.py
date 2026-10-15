"""`tsi ingest ...`: pull CFBD data into the database (cache-first, idempotent)."""

from datetime import UTC, datetime

import typer

from tsi.cli.runtime import ingest_runtime
from tsi.ingest.loaders.calendar import load_calendar
from tsi.ingest.loaders.games import load_games
from tsi.ingest.loaders.lines import load_lines
from tsi.ingest.loaders.priors import load_prior_inputs
from tsi.ingest.loaders.stats import load_team_game_stats
from tsi.ingest.loaders.teams import load_teams
from tsi.ingest.loaders.venues import load_venues
from tsi.services.daily import run_daily

app = typer.Typer(help="Load CFBD data into the database.", no_args_is_help=True)

SEASON = typer.Option(..., "--season", "-s", min=2000, help="Season year, e.g. 2024.")
REFRESH = typer.Option(False, "--refresh", help="Ignore the disk cache and re-fetch (uses calls).")


@app.command()
def daily() -> None:
    """Refresh the in-progress season (what the nightly GitHub Action runs)."""
    with ingest_runtime() as (client, sessions):
        result = run_daily(client, sessions, datetime.now(UTC))
    typer.echo(
        f"daily {result.season}: {result.games} games, {result.stat_rows} stat rows, "
        f"{result.new_line_snapshots} new line snapshots"
        f"{'; teams loaded' if result.loaded_teams else ''}"
        f"{'; calendar loaded' if result.loaded_calendar else ''}"
    )


@app.command()
def venues(refresh: bool = REFRESH) -> None:
    """All venues (one CFBD call, no season)."""
    with ingest_runtime() as (client, sessions):
        count = load_venues(client, sessions, refresh=refresh)
    typer.echo(f"venues: {count} upserted")


@app.command()
def teams(season: int = SEASON, refresh: bool = REFRESH) -> None:
    """Teams and per-season conference/division for one season."""
    with ingest_runtime() as (client, sessions):
        result = load_teams(client, sessions, season, refresh=refresh)
    identity = "updated" if result.identity_updated else "kept (older season)"
    typer.echo(
        f"teams {result.season}: {result.teams} teams, {result.team_seasons} team_seasons; "
        f"team identity {identity}"
    )


@app.command()
def calendar(season: int = SEASON, refresh: bool = REFRESH) -> None:
    """Week boundaries (regular + postseason) for one season."""
    with ingest_runtime() as (client, sessions):
        count = load_calendar(client, sessions, season, refresh=refresh)
    typer.echo(f"calendar {season}: {count} weeks upserted")


@app.command()
def games(season: int = SEASON, refresh: bool = REFRESH) -> None:
    """All regular-season and postseason games for one season."""
    with ingest_runtime() as (client, sessions):
        result = load_games(client, sessions, season, refresh=refresh)
    typer.echo(
        f"games {result.season}: {result.games} games upserted, "
        f"{result.placeholder_teams} placeholder teams added"
    )


@app.command()
def stats(season: int = SEASON, refresh: bool = REFRESH) -> None:
    """Advanced per-game team stats (run after `games` for the same season)."""
    with ingest_runtime() as (client, sessions):
        result = load_team_game_stats(client, sessions, season, refresh=refresh)
    typer.echo(
        f"stats {result.season}: {result.rows} team-game rows upserted, "
        f"{result.unmatched} unmatched CFBD rows"
    )


@app.command()
def lines(season: int = SEASON, refresh: bool = REFRESH) -> None:
    """Betting lines by provider; stores a new snapshot only when numbers change."""
    with ingest_runtime() as (client, sessions):
        result = load_lines(client, sessions, season, refresh=refresh)
    typer.echo(
        f"lines {result.season}: {result.inserted} new snapshots, "
        f"{result.marked_closing} marked closing, {result.unchanged} unchanged"
    )


@app.command()
def priors(season: int = SEASON, refresh: bool = REFRESH) -> None:
    """Preseason prior inputs: talent composite + returning production."""
    with ingest_runtime() as (client, sessions):
        result = load_prior_inputs(client, sessions, season, refresh=refresh)
    typer.echo(
        f"priors {result.season}: {result.talent} talent, {result.returning} returning, "
        f"{result.unmatched} unmatched"
    )
