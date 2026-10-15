"""The `tsi ingest` command group and its shared options."""

import typer

app = typer.Typer(help="Load CFBD data into the database.", no_args_is_help=True)

SEASON = typer.Option(..., "--season", "-s", min=2000, help="Season year, e.g. 2024.")
REFRESH = typer.Option(False, "--refresh", help="Ignore the disk cache and re-fetch (uses calls).")
