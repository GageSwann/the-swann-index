"""Single-endpoint ingest commands (venues, teams, calendar, games, stats, lines, priors)."""

import typer

from tsi.cli.ingest.app import REFRESH, SEASON, app
from tsi.cli.runtime import ingest_runtime
from tsi.ingest.loaders.calendar import load_calendar
from tsi.ingest.loaders.games import load_games
from tsi.ingest.loaders.lines import load_lines
from tsi.ingest.loaders.priors import load_prior_inputs
from tsi.ingest.loaders.stats import load_team_game_stats
from tsi.ingest.loaders.teams import load_teams
from tsi.ingest.loaders.venues import load_venues


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
        r = load_teams(client, sessions, season, refresh=refresh)
    identity = "updated" if r.identity_updated else "kept (older season)"
    typer.echo(
        f"teams {r.season}: {r.teams} teams, {r.team_seasons} team_seasons; identity {identity}"
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
        r = load_games(client, sessions, season, refresh=refresh)
    typer.echo(
        f"games {r.season}: {r.games} games upserted, {r.placeholder_teams} placeholder teams"
    )


@app.command()
def stats(season: int = SEASON, refresh: bool = REFRESH) -> None:
    """Advanced per-game team stats (run after `games` for the same season)."""
    with ingest_runtime() as (client, sessions):
        r = load_team_game_stats(client, sessions, season, refresh=refresh)
    typer.echo(f"stats {r.season}: {r.rows} team-game rows upserted, {r.unmatched} unmatched")


@app.command()
def lines(season: int = SEASON, refresh: bool = REFRESH) -> None:
    """Betting lines by provider; stores a new snapshot only when numbers change."""
    with ingest_runtime() as (client, sessions):
        r = load_lines(client, sessions, season, refresh=refresh)
    typer.echo(
        f"lines {r.season}: {r.inserted} new snapshots, {r.marked_closing} marked closing, "
        f"{r.unchanged} unchanged, {r.skipped} skipped (game not loaded)"
    )


@app.command()
def priors(season: int = SEASON, refresh: bool = REFRESH) -> None:
    """Preseason prior inputs: talent composite + returning production."""
    with ingest_runtime() as (client, sessions):
        r = load_prior_inputs(client, sessions, season, refresh=refresh)
    typer.echo(
        f"priors {r.season}: {r.talent} talent, {r.returning} returning, {r.unmatched} unmatched"
    )
