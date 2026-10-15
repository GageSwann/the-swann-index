"""Root `tsi` command.

Command groups (ingest, run, backtest, ...) live in sibling modules and are
attached here with `app.add_typer(...)` as they are built.
"""

import typer

from tsi import __version__

app = typer.Typer(
    name="tsi",
    help="The Swann Index: college football ratings, predictions, and book.",
    no_args_is_help=True,
    add_completion=False,
)


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
) -> None:
    """The Swann Index: college football ratings, predictions, and book."""
