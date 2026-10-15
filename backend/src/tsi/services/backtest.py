"""Run one model configuration through the walk-forward harness and score it.

Scored set: completed FBS-vs-FBS games with a closing spread, 2015 onward.
Prior coefficients, points-per-Elo and win-probability sigma are fit on TRAIN
seasons only, so VALIDATE seasons are out-of-sample.
"""

from collections.abc import Sequence
from dataclasses import dataclass, replace

from tsi.backtest.ats import AtsRecord, ats_record
from tsi.backtest.calibration import CalibrationBin, calibration_table
from tsi.backtest.evaluate import ScoredGame, Summary, summarize
from tsi.backtest.walk_forward import Pick, walk_forward
from tsi.model.config import ModelConfig
from tsi.model.ratings.probability import fit_sigma, win_prob
from tsi.model.stack import StackSample, fit_stack
from tsi.services.backtest_data import FIRST_DATA_SEASON, BacktestData
from tsi.services.elo_report import TRAIN, VALIDATE
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
        }


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
    picks = walk_forward(data.scored_games, data.rows, priors, config.rating, elo_margins)
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
    rows = [row(str(s), in_seasons(s, s)) for s in sorted({p.game.season for p in picks})]
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
    return BacktestResult(config, sigmas["pred"], rows, calibration, ats, picks)


def _sigma(picks: Sequence[Pick], margin) -> float:
    train = [p for p in picks if TRAIN[0] <= p.game.season <= TRAIN[1]]
    return fit_sigma([margin(p) for p in train], [p.game.margin for p in train])


def stacked_picks(picks: Sequence[Pick], lam: float) -> list[Pick]:
    """Replace the predictive margin with the stacked one, without leaking outcomes.

    TRAIN seasons: leave-one-season-out (each season scored by weights learned on
    the other train seasons). Everything else: weights learned on all of TRAIN.
    """

    def sample(p: Pick) -> StackSample:
        return StackSample(p.bucket, p.features, p.game.margin)

    def in_train(p: Pick) -> bool:
        return TRAIN[0] <= p.game.season <= TRAIN[1]

    train = [p for p in picks if in_train(p)]
    full = fit_stack([sample(p) for p in train], lam)
    held_out = {
        season: fit_stack([sample(p) for p in train if p.game.season != season], lam)
        for season in {p.game.season for p in train}
    }
    out = []
    for p in picks:
        model = held_out[p.game.season] if in_train(p) else full
        out.append(replace(p, predictive_margin=model.predict(p.bucket, p.features)))
    return out
