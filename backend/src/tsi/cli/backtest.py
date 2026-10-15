"""`tsi backtest run`: walk-forward backtest of the full model, saved to model_runs."""

from datetime import UTC, datetime

import typer

from tsi.backtest.ats import BREAK_EVEN
from tsi.backtest.calibration import TOLERANCE
from tsi.cli.runtime import db_runtime
from tsi.ingest.freshness import current_season
from tsi.model.blend import BlendParams
from tsi.model.config import ModelConfig
from tsi.model.ratings.fit import RatingParams
from tsi.services.backtest import BacktestResult, run_backtest
from tsi.services.backtest_data import load_backtest_data
from tsi.services.backtest_store import save_backtest_run

app = typer.Typer(help="Walk-forward backtests.", no_args_is_help=True)


@app.command()
def run(
    through: int | None = typer.Option(None, "--through", help="Last season (default: current)."),
    lam: float = typer.Option(RatingParams.lam, help="Ridge penalty."),
    ppd_weight: float = typer.Option(RatingParams.ppd_weight, help="Share of PPD vs. EPA."),
    prior_games: float = typer.Option(BlendParams.prior_games, help="Prior's weight in games."),
    cutoff_games: float = typer.Option(BlendParams.cutoff_games, help="Games until prior = 0."),
    save: bool = typer.Option(True, help="Save the run to model_runs (kind='backtest')."),
) -> None:
    """TSI `season` + `predictive` vs. Elo and Vegas, plus calibration and ATS (validation)."""
    last = through or current_season(datetime.now(UTC))
    config = ModelConfig(
        RatingParams(lam=lam, ppd_weight=ppd_weight),
        BlendParams(prior_games=prior_games, cutoff_games=cutoff_games),
    )
    with db_runtime() as sessions:
        with sessions() as session:
            data = load_backtest_data(session, last)
        result = run_backtest(data, config)
        run_id = save_backtest_run(sessions, result, last) if save else None

    _print_summary(result)
    _print_calibration(result)
    _print_ats(result)
    if run_id is not None:
        typer.echo(f"\nSaved as model_runs.id={run_id} (kind=backtest)")


def _print_summary(result: BacktestResult) -> None:
    c = result.config
    typer.echo(
        f"TSI {c.to_dict()['version']}: lam={c.rating.lam:g} PPD weight={c.rating.ppd_weight:g} | "
        f"prior {c.blend.prior_games:g} games, gone after {c.blend.cutoff_games:g} | "
        f"sigma {result.sigma:.1f}\n"
        "MAE: Season = this season only (rankings), Pred = with prior (predictions)\n"
    )
    typer.echo(
        f"{'':<24}{'games':>6}  {'Season':>6} {'Pred':>5} {'Elo':>5} {'Vegas':>5}  "
        f"{'Pred%':>5} {'Elo%':>5} {'Veg%':>5}  {'Brier':>5}"
    )
    for r in result.rows:
        s, p, e = r.season, r.predictive, r.elo
        typer.secho(
            f"{s.label:<24}{s.games:>6}  {s.mae:>6.2f} {p.mae:>5.2f} {e.mae:>5.2f} "
            f"{s.market_mae:>5.2f}  {100 * p.su_accuracy:>5.1f} {100 * e.su_accuracy:>5.1f} "
            f"{100 * p.market_su_accuracy:>5.1f}  {p.brier:>5.3f}",
            bold=not s.label[:1].isdigit(),
        )


def _print_calibration(result: BacktestResult) -> None:
    typer.echo(
        f"\nCalibration, validation (favorite's win prob; target ±{100 * TOLERANCE:.0f} pts)"
    )
    for b in result.calibration:
        typer.secho(
            f"  {100 * b.low:3.0f}-{100 * b.high:3.0f}%  games {b.games:>4}  "
            f"predicted {100 * b.predicted:5.1f}%  observed {100 * b.observed:5.1f}%  "
            f"({100 * b.error:+.1f})",
            fg="green" if b.within_tolerance else "yellow",
        )


def _print_ats(result: BacktestResult) -> None:
    typer.echo(f"\nAgainst the closing spread, validation (break-even {100 * BREAK_EVEN:.1f}%)")
    for a in result.ats:
        typer.echo(
            f"  edge >= {a.min_edge:>3.0f} pts: {a.wins}-{a.losses}-{a.pushes}  "
            f"({100 * a.win_rate:.1f}% of {a.bets} bets)"
        )
