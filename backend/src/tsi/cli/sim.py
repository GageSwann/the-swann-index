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
    """Projected wins, conference title and playoff odds for every FBS team (read-only)."""
    with db_runtime() as sessions, sessions() as session:
        projection = project_season(session, datetime.now(UTC), load_artifact(), sims)
    _print(projection, top)


def _print(p: SeasonProjection, top: int) -> None:
    typer.echo(
        f"{p.season} regular season as of week {p.week}: {p.sims:,} simulations, "
        f"rating uncertainty {p.tau:.1f} pts\n"
    )
    typer.echo(
        f"{'Team':<22}{'Conference':<19}{'now':>6}{'left':>5}{'proj W':>8}{'80% range':>11}"
        f"{'win out':>9}{'in CCG':>8}{'champ':>8}{'CFP':>8}{'bye':>8}{'title':>8}"
    )
    for t in p.teams[: top or None]:
        typer.echo(_row(t, p.names.get(t.team_id, str(t.team_id))))


def _row(t: TeamProjection, name: str) -> str:
    lo, hi = _central(t.win_dist, 0.8)
    rec = f"{t.record.wins}-{t.record.losses}"
    return (
        f"{name:<22}{(t.conference or '')[:18]:<19}{rec:>6}{t.remaining:>5}{t.expected_wins:>8.1f}"
        f"{f'{lo}-{hi}':>11}{_pct(t.win_out_prob):>9}{_pct(t.title_game_prob):>8}"
        f"{_pct(t.conference_title_prob):>8}"
        + "".join(
            f"{_pct(getattr(t.playoff, f) if t.playoff else None):>8}"
            for f in ("make", "bye", "champion")
        )
    )


def _pct(p: float | None) -> str:
    return "—" if p is None else f"{100 * p:.1f}%"


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
