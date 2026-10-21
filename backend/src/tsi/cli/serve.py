"""`tsi serve`: run the read-only API locally (uvicorn)."""

import typer


def serve(
    host: str = typer.Option("127.0.0.1", help="Interface to bind."),
    port: int = typer.Option(8000, help="Port."),
    reload: bool = typer.Option(False, help="Restart on code changes (development)."),
) -> None:
    """Serve the API at http://HOST:PORT (interactive docs at /docs)."""
    import uvicorn

    uvicorn.run("tsi.api.app:create_app", factory=True, host=host, port=port, reload=reload)
