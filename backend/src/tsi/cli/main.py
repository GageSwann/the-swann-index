"""Root `tsi` command.

Command groups (ingest, run, backtest, ...) live in sibling modules and are
attached here with `app.add_typer(...)` as they are built.
"""

import typer

from tsi import __version__
from tsi.cli import ingest
from tsi.cli.runtime import configure_logging

app = typer.Typer(
    name="tsi",
    help="The Swann Index: college football ratings, predictions, and book.",
    no_args_is_help=True,
    add_completion=False,
)
app.add_typer(ingest.app, name="ingest")


def _print_version(value: bool) -> None:
    if value:
        typer.echo(f"tsi {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the TSI version and exit.",
        callback=_print_version,
        is_eager=True,
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Debug logging."),
) -> None:
    """The Swann Index: college football ratings, predictions, and book."""
    configure_logging(verbose)
