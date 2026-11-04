"""`tsi adjust ...`: the operator's manual adjustments (injuries, QB changes; decision #103)."""

from datetime import UTC, date, datetime, time, timedelta

import typer

from tsi.cli.runtime import db_runtime, fail
from tsi.db.queries.adjustments import StoredAdjustment
from tsi.ingest.freshness import current_season
from tsi.services.adjust import (
    AdjustmentError,
    NewAdjustment,
    add_adjustment,
    expire_adjustment,
    list_adjustments,
)
from tsi.services.read.adjustment_report import AdjustedScore, season_adjustment_report

app = typer.Typer(help="Manual adjustments on top of the model.", no_args_is_help=True)

# A football day runs 10:00 to 10:00 UTC (the nightly run), so a date covers every kickoff
# that day in US time, late West Coast and Hawaii games included.
DAY_TURNS = time(10, tzinfo=UTC)


@app.command()
def add(
    team: str = typer.Argument(..., help="Team slug, e.g. ohio-state."),
    reason: str = typer.Option(..., "--reason", "-r", help="Shown next to the adjusted numbers."),
    off: float = typer.Option(0.0, "--off", help="Points per game for its offense (QB out: -4)."),
    defense: float = typer.Option(0.0, "--def", help="Points per game for its defense."),
    start: str | None = typer.Option(
        None, "--from", help="First game day covered, YYYY-MM-DD (default: now)."
    ),
    through: str | None = typer.Option(
        None, "--through", help="Last game day covered, YYYY-MM-DD (default: rest of season)."
    ),
) -> None:
    """Add an adjustment for a team's upcoming games."""
    now = datetime.now(UTC)
    new = NewAdjustment(
        team_slug=team,
        off_points=off,
        def_points=defense,
        reason=reason,
        starts_at=start and _day_start(_date(start, "--from")),
        ends_at=through and _day_start(_date(through, "--through") + timedelta(days=1)),
    )
    with db_runtime() as sessions:
        try:
            adjustment_id = add_adjustment(sessions, new, now)
        except AdjustmentError as exc:
            raise fail(str(exc)) from None
        with sessions() as session:
            added = next(
                a
                for a in list_adjustments(session, now, include_ended=True)
                if a.id == adjustment_id
            )
    typer.echo(f"Added #{adjustment_id}:")
    typer.echo(_line(added))
    typer.echo("Takes effect at the next publish (`tsi run` or `tsi book publish`).")


@app.command(name="list")
def list_(
    all_: bool = typer.Option(False, "--all", help="Include adjustments that have ended."),
    season: int | None = typer.Option(None, help="Season (default: current)."),
) -> None:
    """This season's adjustments that are still in effect (or all of them)."""
    now = datetime.now(UTC)
    with db_runtime() as sessions, sessions() as session:
        rows = list_adjustments(session, now, include_ended=all_, season=season)
    if not rows:
        typer.echo("No adjustments" + ("." if all_ else " in effect (--all shows ended ones)."))
        return
    typer.echo(f"{'#':>4}  {'Team':<20}{'off':>6}{'def':>6}{'net':>6}  {'covers':<33}  Reason")
    for a in rows:
        typer.echo(_line(a, now))


@app.command()
def expire(adjustment_id: int = typer.Argument(..., help="The # from `tsi adjust list`.")) -> None:
    """End an adjustment now. Games already played keep it; upcoming games drop it."""
    now = datetime.now(UTC)
    with db_runtime() as sessions:
        try:
            expire_adjustment(sessions, adjustment_id, now)
        except AdjustmentError as exc:
            raise fail(str(exc)) from None
    typer.echo(f"Expired #{adjustment_id}; the next publish drops it from upcoming games.")


@app.command()
def report(season: int | None = typer.Option(None, help="Season (default: current).")) -> None:
    """Did the adjustments help? Raw model vs. adjusted on finished adjusted games."""
    now = datetime.now(UTC)
    with db_runtime() as sessions, sessions() as session:
        r = season_adjustment_report(session, season or current_season(now), now)
    if r.overall.games == 0:
        typer.echo("No finished games with an adjusted prediction yet.")
        return
    typer.echo(f"{'':<34}{'games':>6}{'margin err':>18}{'total err':>16}{'winners':>16}  helped")
    typer.echo(f"{'(raw -> adjusted)':<34}" + _score(r.overall))
    for a in r.adjustments:
        n = a.adjustment
        typer.echo(f"#{n.id:<3}{n.school[:14]:<15}{n.reason[:15]:<16}" + _score(a.score))


def _score(s: AdjustedScore) -> str:
    def pair(raw: float | None, adj: float | None, pct: bool = False) -> str:
        if raw is None or adj is None:
            return "-"
        return f"{100 * raw:.0f}% -> {100 * adj:.0f}%" if pct else f"{raw:.2f} -> {adj:.2f}"

    return (
        f"{s.games:>6}{pair(s.raw_mae, s.adjusted_mae):>18}"
        f"{pair(s.raw_total_mae, s.adjusted_total_mae):>16}"
        f"{pair(s.raw_su, s.adjusted_su, pct=True):>16}  {s.helped}-{s.hurt}-{s.same}"
    )


def _date(text: str, option: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise fail(f"{option} needs a date like 2026-11-14, not '{text}'.") from None


def _day_start(day: date) -> datetime:
    return datetime.combine(day, DAY_TURNS)


def _line(a: StoredAdjustment, now: datetime | None = None) -> str:
    ended = now is not None and a.ends_at is not None and a.ends_at <= now
    return (
        f"{a.id:>4}  {a.school[:19]:<20}{a.off_points:>+6.1f}{a.def_points:>+6.1f}{a.points:>+6.1f}"
        f"  {_window(a):<33}  {a.reason}" + ("  (ended)" if ended else "")
    )


def _window(a: StoredAdjustment) -> str:
    start = f"{a.starts_at:%b %d %H:%M}"
    if a.ends_at is None:
        return f"{start} UTC on"
    return f"{start} to {a.ends_at:%b %d %H:%M} UTC"
