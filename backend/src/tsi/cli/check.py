"""`tsi check`: run data quality checks; exits 1 if any `fail` rule finds problems."""

import typer

from tsi.config import ConfigError, get_settings
from tsi.db.engine import make_engine, make_session_factory
from tsi.quality.runner import CheckResult, run_checks

COLORS = {"PASS": "green", "WARN": "yellow", "FAIL": "red"}


def check(
    season: int | None = typer.Option(None, "--season", "-s", help="Only this season."),
    details: bool = typer.Option(False, "--details", "-d", help="Show example rows."),
) -> None:
    """Run data quality checks (doc 03). Fails on correctness problems, warns on source gaps."""
    try:
        settings = get_settings()
    except ConfigError as exc:
        typer.secho(str(exc), fg="red", err=True)
        raise typer.Exit(1) from None

    engine = make_engine(settings)
    try:
        with make_session_factory(engine)() as session:
            results = run_checks(session, season)
    finally:
        engine.dispose()

    for result in results:
        _print_result(result, details)
    failures = sum(r.failed for r in results)
    warnings = sum(r.check.severity == "warn" and r.count > 0 for r in results)
    typer.echo(f"\n{len(results)} checks: {failures} failed, {warnings} with warnings")
    if failures:
        raise typer.Exit(1)


def _print_result(result: CheckResult, details: bool) -> None:
    status = "PASS" if result.count == 0 else "FAIL" if result.failed else "WARN"
    seasons = ", ".join(f"{s}: {n}" for s, n in result.by_season.items())
    line = f"[{status}] {result.check.description}"
    if result.count:
        line += f" ({result.count}; by season: {seasons})"
    typer.secho(line, fg=COLORS[status])
    if details:
        for example in result.examples:
            typer.echo(f"         {example}")
