"""`tsi neon ...`: read-only checks on the Neon project (network transfer, #140)."""

import json
from datetime import UTC, datetime

import typer

from tsi.config import load_settings
from tsi.ops.neon_api import NeonApiError, fetch_project_usage
from tsi.ops.transfer_pace import FREE_LIMIT_BYTES, GB, assess, describe

app = typer.Typer(help="Read-only checks on the Neon project.", no_args_is_help=True)


@app.command()
def transfer(
    as_json: bool = typer.Option(False, "--json", help="One JSON object (for the workflow)."),
    limit_gb: float = typer.Option(FREE_LIMIT_BYTES / GB, help="Monthly limit in GB."),
) -> None:
    """This period's network transfer and its pace against the limit (one Neon API call).
    Exits 0 whatever the pace: the caller decides what to do with an alert. Exits 2 when
    NEON_API_KEY / NEON_PROJECT_ID are unset, 1 when Neon doesn't answer."""
    settings = load_settings()
    if settings.neon_api_key is None or not settings.neon_project_id:
        typer.echo("Skipped: NEON_API_KEY and NEON_PROJECT_ID are not both set.", err=True)
        raise typer.Exit(2)
    try:
        usage = fetch_project_usage(settings.neon_api_key, settings.neon_project_id)
    except NeonApiError as exc:
        typer.echo(f"Neon transfer check failed: {exc}", err=True)
        raise typer.Exit(1) from None
    reading = assess(usage, datetime.now(UTC), limit_bytes=round(limit_gb * GB))
    typer.echo(json.dumps(reading.to_dict()) if as_json else describe(reading))
