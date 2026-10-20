"""What one walk-forward backtest run produces, and the headline metrics saved with it."""

from dataclasses import dataclass

from tsi.backtest.ats import AtsRecord
from tsi.backtest.calibration import CalibrationBin
from tsi.backtest.evaluate import Summary
from tsi.backtest.market_calibration import LineCheck
from tsi.backtest.totals_eval import TotalsSummary
from tsi.backtest.walk_forward import Pick
from tsi.model.config import ModelConfig
from tsi.model.distribution import DistributionParams


@dataclass(frozen=True)
class ComparisonRow:
    season: Summary  # TSI `season` set (this season only; drives rankings)
    predictive: Summary  # TSI `predictive` margin (stack; drives predictions)
    elo: Summary


@dataclass(frozen=True)
class BacktestResult:
    config: ModelConfig
    distribution: DistributionParams  # score distribution (fit on train)
    rows: list[ComparisonRow]
    calibration: list[CalibrationBin]  # predictive, validation seasons
    ats: list[AtsRecord]  # predictive vs. closing line, validation seasons
    totals: list[TotalsSummary]  # predictive total vs. closing total, by season + period
    lines: LineCheck  # edge shrink (train) + Book cover/over calibration at the opener
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
            "sigma": self.distribution.sigma_margin,
            "sigma_total": self.distribution.sigma_total,
            "sigma_total_slope": self.distribution.sigma_total_slope,
            "rho_per_point": self.distribution.rho_per_point,
            "k_spread": self.lines.shrink.k_spread,
            "k_total": self.lines.shrink.k_total,
            "validate_total_mae": self.validation_totals.mae,
            "validate_total_market_mae": self.validation_totals.market_mae,
            "validate_ou": self.validation_totals.ou_accuracy,
        }

    @property
    def validation_totals(self) -> TotalsSummary:
        return next(t for t in self.totals if t.label.startswith("Validate"))
