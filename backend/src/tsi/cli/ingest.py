"""`tsi ingest ...`: pull CFBD data into the database (cache-first, idempotent)."""

import typer

from tsi.cli.runtime import ingest_runtime
from tsi.ingest.loaders.calendar import load_calendar
from tsi.ingest.loaders.games import load_games
from tsi.ingest.loaders.teams import load_teams
from tsi.ingest.loaders.venues import load_venues

app = typer.Typer(help="Load CFBD data into the database.", no_args_is_help=True)

SEASON = typer.Option(..., "--season", "-s", min=2000, help="Season year, e.g. 2024.")
REFRESH = typer.Option(False, "--refresh", help="Ignore the disk cache and re-fetch (uses calls).")


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
