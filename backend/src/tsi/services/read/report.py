"""`/model/report`: the latest backtest (headline metrics + report tables), the model
version history, and how the published predictions are doing.

Backtest = the latest saved `tsi backtest run` (model_runs kind 'backtest').
Live = this season's finished games scored from their locked snapshots: TSI vs.
the result and vs. the closing consensus (median of books). Adjustments = raw vs.
adjusted on the games that were manually adjusted (decision #105).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import ModelRun
from tsi.db.queries.games import GameRow, season_games
from tsi.db.queries.snapshots import SnapshotRow, snapshots_for_season
from tsi.services.read.adjustment_report import AdjustmentReport, adjustment_report
from tsi.services.read.backtest_report import (
    BacktestReport,
    ModelVersion,
    model_versions,
    parse_report,
)
from tsi.services.read.common import current_snapshot, market_lines, mean_or_none


@dataclass(frozen=True)
class BacktestSummary:
    run_at: datetime
    model_version: str
    git_sha: str | None
    metrics: dict[str, float]  # e.g. validate_mae, validate_market_mae, validate_su, sigma, k_total
    report: BacktestReport | None  # None for runs saved before report tables were stored


@dataclass(frozen=True)
class LiveAccuracy:
    games: int  # finished games with a locked snapshot
    mae: float | None  # |TSI margin - actual|
    market_mae: float | None  # |closing spread - actual|, same games with a closing line
    su_accuracy: float | None  # TSI favorite won (ties excluded)


@dataclass(frozen=True)
class ModelReport:
    season: int
    backtest: BacktestSummary | None
    live: LiveAccuracy
    versions: list[ModelVersion]
    adjustments: AdjustmentReport  # raw vs. adjusted on manually adjusted games


def model_report(session: Session, season: int, now: datetime) -> ModelReport:
    snaps = snapshots_for_season(session, season)
    games = season_games(session, season, list(snaps))
    return ModelReport(
        season,
        _latest_backtest(session),
        _live(session, games, snaps, now),
        model_versions(session),
        adjustment_report(session, games, snaps, now),
    )


def _latest_backtest(session: Session) -> BacktestSummary | None:
    row = session.execute(
        select(ModelRun.run_at, ModelRun.model_version, ModelRun.git_sha, ModelRun.params)
        .where(ModelRun.kind == "backtest")
        .order_by(ModelRun.run_at.desc(), ModelRun.id.desc())
        .limit(1)
    ).first()
    if row is None:
        return None
    params: dict[str, Any] = row[3] or {}
    metrics = {k: float(v) for k, v in params.get("metrics", {}).items() if v is not None}
    return BacktestSummary(row[0], row[1], row[2], metrics, parse_report(params.get("report", {})))


def _live(
    session: Session, games: list[GameRow], snaps: dict[int, list[SnapshotRow]], now: datetime
) -> LiveAccuracy:
    """The raw model's locked predictions of finished games vs. the result and the close."""
    scored: list[tuple[GameRow, SnapshotRow]] = []
    for g in games:
        if not g.completed or g.home_points is None or g.away_points is None:
            continue
        official, locked = current_snapshot(snaps.get(g.id, []), g.start_time, now)
        if official is not None and locked:
            scored.append((g, official.raw or official))  # the model's own: never adjusted
    closing = market_lines(session, [g for g, _ in scored], now) if scored else {}
    errs, market_errs, su = [], [], []
    for g, snap in scored:
        margin = g.home_points - g.away_points
        errs.append(abs(-snap.spread - margin))
        if margin != 0 and snap.spread != 0:
            su.append(float((margin > 0) == (snap.spread < 0)))
        line = closing.get(g.id)
        if line and line.spread is not None:
            market_errs.append(abs(-line.spread - margin))
    return LiveAccuracy(len(errs), mean_or_none(errs), mean_or_none(market_errs), mean_or_none(su))
