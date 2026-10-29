"""`tsi sim ...`: season Monte Carlo from today's forecasts."""

from datetime import UTC, datetime

import typer

from tsi.cli.runtime import db_runtime
from tsi.model.artifact import load_artifact
from tsi.services.season_sim import SeasonProjection, TeamProjection, project_season
from tsi.sim.season import DEFAULT_SIMS

app = typer.Typer(help="Season simulation.", no_args_is_help=True)


@app.command()
def season(
    sims: int = typer.Option(DEFAULT_SIMS, help="Simulated seasons."),
    top: int = typer.Option(25, help="Teams to show (most projected wins first); 0 = all."),
) -> None:
    """Projected regular-season wins for every FBS team (read-only)."""
    with db_runtime() as sessions, sessions() as session:
        projection = project_season(session, datetime.now(UTC), load_artifact(), sims)
    _print(projection, top)


def _print(p: SeasonProjection, top: int) -> None:
    typer.echo(
        f"{p.season} regular season as of week {p.week}: {p.sims:,} simulations, "
        f"rating uncertainty {p.tau:.1f} pts\n"
    )
    typer.echo(f"{'Team':<22}{'now':>6}{'left':>5}{'proj W':>8}{'80% range':>11}{'win out':>9}")
    for t in p.teams[: top or None]:
        typer.echo(_row(t, p.names.get(t.team_id, str(t.team_id))))


def _row(t: TeamProjection, name: str) -> str:
    lo, hi = _central(t.win_dist, 0.8)
    win_out = t.win_dist[-1] if t.remaining else 1.0
    rec = f"{t.record.wins}-{t.record.losses}"
    return (
        f"{name:<22}{rec:>6}{t.remaining:>5}{t.expected_wins:>8.1f}"
        f"{f'{lo}-{hi}':>11}{100 * win_out:>8.1f}%"
    )


def _central(dist: list[float], mass: float) -> tuple[int, int]:
    """Smallest and largest win totals bounding the central `mass` of the distribution."""
    tail = (1 - mass) / 2
    cum, lo, hi = 0.0, None, 0
    for k, p in enumerate(dist):
        cum += p
        if lo is None and cum > tail:
            lo = k
        if cum < 1 - tail:
            hi = k + 1
    return lo or 0, min(hi, len(dist) - 1)
