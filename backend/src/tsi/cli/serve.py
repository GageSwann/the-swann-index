"""`tsi serve` (run the read-only API locally) and `tsi openapi` (export its spec)."""

from pathlib import Path

import typer

from tsi.api.openapi import SPEC_PATH

SPEC_OUT = typer.Option(SPEC_PATH, help="Where to write the spec (commit it).")


def serve(
    host: str = typer.Option("127.0.0.1", help="Interface to bind."),
    port: int = typer.Option(8000, help="Port."),
    reload: bool = typer.Option(False, help="Restart on code changes (development)."),
) -> None:
    """Serve the API at http://HOST:PORT (interactive docs at /docs)."""
    import uvicorn

    uvicorn.run("tsi.api.app:create_app", factory=True, host=host, port=port, reload=reload)


def openapi(
    out: Path = SPEC_OUT,
) -> None:
    """Write the OpenAPI spec (no database needed); the web generates its TS types from it."""
    from tsi.api.openapi import write_openapi

    path = write_openapi(out)
    typer.echo(f"Wrote {path}")
