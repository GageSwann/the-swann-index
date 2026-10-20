"""Run one model configuration through the walk-forward harness and score it.

Scored set: completed FBS-vs-FBS games with a closing spread, 2015 onward
(totals: the subset that also has a closing total).
Prior coefficients, points-per-Elo and win-probability sigma are fit on TRAIN
seasons only, so VALIDATE seasons are out-of-sample.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from tsi.backtest.ats import AtsRecord, ats_record
from tsi.backtest.calibration import CalibrationBin, calibration_table
from tsi.backtest.evaluate import ScoredGame, Summary, summarize
from tsi.backtest.splits import TRAIN, VALIDATE
from tsi.backtest.stacking import stacked_picks
from tsi.backtest.totals_eval import TotalsSummary, summarize_totals
from tsi.backtest.walk_forward import Pick, walk_forward
from tsi.model.config import ModelConfig
from tsi.model.ratings.probability import fit_sigma, win_prob
from tsi.services.backtest_data import FIRST_DATA_SEASON, BacktestData
from tsi.services.prior_setup import build_prior_setup

ATS_EDGES = (0.0, 3.0, 5.0)


@dataclass(frozen=True)
class ComparisonRow:
    season: Summary  # TSI `season` set (this season only; drives rankings)
    predictive: Summary  # TSI `predictive` margin (stack; drives predictions)
    elo: Summary


@dataclass(frozen=True)
class BacktestResult:
    config: ModelConfig
    sigma: float  # predictive win-prob sigma (fit on train)
    rows: list[ComparisonRow]
    calibration: list[CalibrationBin]  # predictive, validation seasons
    ats: list[AtsRecord]  # predictive vs. closing line, validation seasons
    totals: list[TotalsSummary]  # predictive total vs. closing total, by season + period
    picks: list[Pick]

    @property
    def validation(self) -> ComparisonRow:
        return next(r for r in self.rows if r.season.label.startswith("Validate"))

    @property
    def train(self) -> ComparisonRow:
        return next(r for r in self.rows if r.season.label.startswith("Train"))

    def metrics(self) -> dict[str, float]:
        v, t = self.validation.predictive, self.train.predictive
        return {
            "train_mae": t.mae,
            "validate_mae": v.mae,
            "validate_market_mae": v.market_mae,
            "validate_su": v.su_accuracy,
            "validate_brier": v.brier,
            "validate_ats": self.ats[0].win_rate,
            "sigma": self.sigma,
            "validate_total_mae": self.validation_totals.mae,
            "validate_total_market_mae": self.validation_totals.market_mae,
            "validate_ou": self.validation_totals.ou_accuracy,
        }

    @property
    def validation_totals(self) -> TotalsSummary:
        return next(t for t in self.totals if t.label.startswith("Validate"))


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
    return BacktestResult(config, sigmas["pred"], rows, calibration, ats, totals, picks)


def _sigma(picks: Sequence[Pick], margin) -> float:
    train = [p for p in picks if TRAIN[0] <= p.game.season <= TRAIN[1]]
    return fit_sigma([margin(p) for p in train], [p.game.margin for p in train])
