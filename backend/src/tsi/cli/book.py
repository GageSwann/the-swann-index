"""`tsi book`: publish prediction snapshots + picks, and grade them after the final."""

from datetime import UTC, datetime

import typer

from tsi.cli.runtime import db_runtime
from tsi.model.artifact import load_artifact
from tsi.services.board import DEFAULT_DAYS, BoardGame, build_board
from tsi.services.grade import grade_picks
from tsi.services.publish import publish_board

app = typer.Typer(
    help="TSI Book: publish predictions and picks, grade results.", no_args_is_help=True
)


@app.command()
def publish(
    days: int = typer.Option(DEFAULT_DAYS, help="Publish games kicking off within N days."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the board; don't save."),
    show: int = typer.Option(15, help="How many games to print."),
) -> None:
    """Forecast upcoming games, price them, compare with the market, publish new snapshots."""
    now = datetime.now(UTC)
    artifact = load_artifact()
    with db_runtime() as sessions:
        with sessions() as session:
            board = build_board(session, now, artifact, days)
        result = None if dry_run else publish_board(sessions, board.games, now, artifact)

    names = board.names
    typer.echo(f"{len(board.games)} games in the next {days} days as of {now:%Y-%m-%d %H:%M} UTC")
    typer.echo(f"{'Matchup':<40}{'TSI':>14}{'Market':>14}  Picks")
    for b in board.games[:show]:
        typer.echo(_line(b, names))
    picks = [p for b in board.games for p in b.picks]
    typer.echo(f"\nTSI Plays: {len(picks)} ({', '.join(_tier_counts(picks)) or 'none'})")
    if result is not None:
        typer.echo(
            f"Published {result.published} snapshots ({result.unchanged} unchanged), "
            f"{result.picks} picks" + (f", model_runs.id={result.run_id}" if result.run_id else "")
        )


@app.command()
def grade() -> None:
    """Grade official (locked-snapshot) picks of finished games; record the closing line."""
    with db_runtime() as sessions:
        r = grade_picks(sessions, datetime.now(UTC))
    typer.echo(
        f"Graded {r.graded} picks: {r.wins}-{r.losses}-{r.pushes}, {r.units:+.2f} units (flat)"
    )


def _line(b: BoardGame, names: dict[int, str]) -> str:
    g, d, m = b.forecast.game, b.forecast.distribution, b.market
    matchup = f"{names[g.away_id][:17]} {'vs' if g.neutral else 'at'} {names[g.home_id][:17]}"
    tsi = f"{-d.margin:+.1f} / {d.total:.1f}"
    market = "-" if m.spread is None else f"{m.spread:+.1f} / {m.total or 0:.1f}"
    picks = ", ".join(f"{p.market} {p.side} {'*' * p.tier}" for p in b.picks)
    return f"{matchup:<40}{tsi:>14}{market:>14}  {picks}"


def _tier_counts(picks) -> list[str]:
    return [
        f"{sum(p.tier == t for p in picks)} {'*' * t}"
        for t in (3, 2, 1)
        if any(p.tier == t for p in picks)
    ]
