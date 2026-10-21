"""Typed views of the report tables saved with a backtest run (`params.report`, written by
`services/report_tables.py`), and the model version history from saved backtests."""

from dataclasses import dataclass, fields
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import ModelRun


@dataclass(frozen=True)
class AccuracyRow:
    label: str  # a season ("2024") or a period ("Validate 2023–25")
    games: int
    season_mae: float  # this-season-only ratings (rankings)
    predictive_mae: float  # the stacked prediction (what TSI publishes)
    elo_mae: float
    vegas_mae: float  # closing consensus
    predictive_su: float
    elo_su: float
    vegas_su: float
    predictive_brier: float


@dataclass(frozen=True)
class CalibrationBin:
    bin: str  # "60–70%"
    games: int
    predicted: float
    observed: float


@dataclass(frozen=True)
class AtsRow:
    min_edge: float  # points of disagreement with the closing spread
    bets: int
    wins: int
    losses: int
    pushes: int
    win_rate: float


@dataclass(frozen=True)
class TotalsRow:
    period: str
    games: int
    tsi_mae: float
    vegas_mae: float
    bias: float  # mean (TSI total − actual)
    ou_vs_close: float  # share on the right side of the closing total


@dataclass(frozen=True)
class BookBacktestRow:
    period: str  # "Train 2021–22", "Validate 2023–25" or a season
    market: str  # 'all' or a market
    tier: int  # 0 = all tiers
    bets: int
    wins: int
    losses: int
    pushes: int
    win_rate: float
    units: float
    roi: float
    kelly_units: float
    clv: float | None
    beat_close: float | None


@dataclass(frozen=True)
class BookCalibrationBin:
    market: str  # 'spread' (P home covers) | 'total' (P over), at the opener
    bin: str
    games: int
    predicted: float
    observed: float


@dataclass(frozen=True)
class BookUnitsPoint:
    date: date
    season: int
    units: float  # cumulative flat units since the first season with openers
    kelly_units: float


@dataclass(frozen=True)
class BacktestReport:
    by_season: list[AccuracyRow]
    periods: list[AccuracyRow]
    calibration: list[CalibrationBin]
    ats: list[AtsRow]
    totals: list[TotalsRow]
    book: list[BookBacktestRow]
    book_calibration: list[BookCalibrationBin]
    book_units: list[BookUnitsPoint]


@dataclass(frozen=True)
class ModelVersion:
    model_version: str
    run_at: datetime  # latest backtest of this version
    git_sha: str | None
    validate_mae: float | None
    validate_market_mae: float | None
    validate_su: float | None


def parse_report(tables: dict[str, list[dict[str, Any]]]) -> BacktestReport | None:
    """None for runs saved before report tables were stored."""
    if not tables:
        return None
    return BacktestReport(
        by_season=[_accuracy(str(r["season"]), r) for r in tables.get("by_season", [])],
        periods=[_accuracy(r["period"], r) for r in tables.get("periods", [])],
        calibration=_rows(CalibrationBin, tables.get("calibration", [])),
        ats=_rows(AtsRow, tables.get("ats", [])),
        totals=_rows(TotalsRow, tables.get("totals_accuracy", [])),
        book=_rows(BookBacktestRow, tables.get("book_record", [])),
        book_calibration=_rows(BookCalibrationBin, tables.get("book_calibration", [])),
        book_units=[
            BookUnitsPoint(date.fromisoformat(r["date"]), r["season"], r["units"], r["kelly_units"])
            for r in tables.get("book_units", [])
        ],
    )


def _accuracy(label: str, row: dict[str, Any]) -> AccuracyRow:
    return AccuracyRow(label, **{f.name: row[f.name] for f in fields(AccuracyRow)[1:]})


def _rows[T](cls: type[T], rows: list[dict[str, Any]]) -> list[T]:
    names = [f.name for f in fields(cls)]  # type: ignore[arg-type]
    return [cls(**{n: r.get(n) for n in names}) for r in rows]


def model_versions(session: Session) -> list[ModelVersion]:
    """The latest saved backtest of each model version, oldest version first."""
    rows = session.execute(
        select(ModelRun.model_version, ModelRun.run_at, ModelRun.git_sha, ModelRun.params)
        .where(ModelRun.kind == "backtest")
        .order_by(ModelRun.run_at, ModelRun.id)
    ).all()
    latest: dict[str, ModelVersion] = {}
    for version, run_at, sha, params in rows:
        m = (params or {}).get("metrics", {})
        latest[version] = ModelVersion(
            version,
            run_at,
            sha,
            m.get("validate_mae"),
            m.get("validate_market_mae"),
            m.get("validate_su"),
        )
    return sorted(latest.values(), key=lambda v: v.run_at)
