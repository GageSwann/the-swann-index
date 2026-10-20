"""Run one model configuration through the walk-forward harness and score it.

Scored set: completed FBS-vs-FBS games with a closing spread, 2015 onward
(totals: the subset that also has a closing total).
Prior coefficients, points-per-Elo and the score distribution are fit on TRAIN
seasons only, so VALIDATE seasons are out-of-sample.
"""

from collections.abc import Sequence

from tsi.backtest.ats import ats_record
from tsi.backtest.calibration import calibration_table
from tsi.backtest.evaluate import ScoredGame, summarize
from tsi.backtest.market_calibration import line_check
from tsi.backtest.splits import TRAIN, VALIDATE
from tsi.backtest.stacking import stacked_picks
from tsi.backtest.totals_eval import summarize_totals
from tsi.backtest.walk_forward import Pick, walk_forward
from tsi.model.config import ModelConfig
from tsi.model.distribution_fit import fit_distribution
from tsi.model.ratings.probability import fit_sigma, win_prob
from tsi.services.backtest_data import FIRST_DATA_SEASON, BacktestData
from tsi.services.backtest_result import BacktestResult, ComparisonRow
from tsi.services.prior_setup import build_prior_setup

ATS_EDGES = (0.0, 3.0, 5.0)


def run_backtest(data: BacktestData, config: ModelConfig | None = None) -> BacktestResult:
    config = config or ModelConfig()
    setup = build_prior_setup(
        data.rows,
        range(FIRST_DATA_SEASON, data.through_season),
        data.fbs,
        data.prior_table,
        TRAIN,
        config.rating,
    )
    priors = {
        s: setup.priors_for(s, data.fbs.get(s, set()), data.prior_table)
        for s in range(TRAIN[0], data.through_season + 1)
    }
    elo_margins = {gid: pick.margin for gid, pick in data.elo.items()}
    picks = walk_forward(
        data.scored_games, data.rows, priors, config.rating, elo_margins, setup.final_components
    )
    picks = stacked_picks(picks, config.stack_lam)
    sigmas = {
        "season": _sigma(picks, lambda p: p.season_margin),
        "pred": _sigma(picks, lambda p: p.predictive_margin),
    }

    def scored(subset: Sequence[Pick], model: str) -> list[ScoredGame]:
        out = []
        for p in subset:
            g, market = p.game, -data.closing[p.game.id]
            if model == "elo":
                margin, prob = data.elo[g.id].margin, data.elo[g.id].home_win_prob
            else:
                margin = p.season_margin if model == "season" else p.predictive_margin
                prob = win_prob(margin, sigmas[model])
            out.append(ScoredGame(g.season, margin, prob, g.margin, market))
        return out

    def row(label: str, subset: Sequence[Pick]) -> ComparisonRow:
        return ComparisonRow(
            *(summarize(label, scored(subset, m)) for m in ("season", "pred", "elo"))
        )

    def in_seasons(first: int, last: int) -> list[Pick]:
        return [p for p in picks if first <= p.game.season <= last]

    validate = in_seasons(*VALIDATE)
    seasons = sorted({p.game.season for p in picks})
    rows = [row(str(s), in_seasons(s, s)) for s in seasons]
    rows += [
        row(f"Train {TRAIN[0]}-{TRAIN[1]}", in_seasons(*TRAIN)),
        row(f"Validate {VALIDATE[0]}-{VALIDATE[1]}", validate),
        row("  both teams 4+ games", [p for p in validate if p.established]),
        row("  provisional (<4)", [p for p in validate if not p.established]),
    ]
    v_scored = scored(validate, "pred")
    outcomes = [
        1.0 if g.actual_margin > 0 else 0.0 if g.actual_margin < 0 else 0.5 for g in v_scored
    ]
    calibration = calibration_table([g.home_win_prob for g in v_scored], outcomes)
    ats = [
        ats_record(
            [g.pred_margin for g in v_scored],
            [g.market_margin for g in v_scored],
            [g.actual_margin for g in v_scored],
            edge,
        )
        for edge in ATS_EDGES
    ]
    totals = [summarize_totals(str(s), in_seasons(s, s), data.closing_totals) for s in seasons]
    totals += [
        summarize_totals(f"Train {TRAIN[0]}-{TRAIN[1]}", in_seasons(*TRAIN), data.closing_totals),
        summarize_totals(f"Validate {VALIDATE[0]}-{VALIDATE[1]}", validate, data.closing_totals),
    ]
    train = in_seasons(*TRAIN)
    distribution = fit_distribution(
        sigmas["pred"],
        [p.predictive_margin for p in train],
        [p.game.margin for p in train],
        [p.predictive_total for p in train],
        [p.game.home_points + p.game.away_points for p in train],
    )
    return BacktestResult(
        config,
        distribution,
        rows,
        calibration,
        ats,
        totals,
        line_check(
            train,
            validate,
            distribution,
            {g: o.spread for g, o in data.opening.items()},
            {g: o.total for g, o in data.opening.items()},
        ),
        picks,
    )


def _sigma(picks: Sequence[Pick], margin) -> float:
    train = [p for p in picks if TRAIN[0] <= p.game.season <= TRAIN[1]]
    return fit_sigma([margin(p) for p in train], [p.game.margin for p in train])
