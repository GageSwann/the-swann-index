"""`/model/report`: the latest backtest (headline metrics + report tables), the model
version history, and how the published predictions are doing.

Backtest = the latest saved `tsi backtest run` (model_runs kind 'backtest').
Live = this season's finished games scored from their locked snapshots: TSI vs.
the result and vs. the closing consensus (median of books).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import ModelRun
from tsi.db.queries.games import season_games
from tsi.db.queries.snapshots import snapshots_for_season
from tsi.services.read.backtest_report import (
    BacktestReport,
    ModelVersion,
    model_versions,
    parse_report,
)
from tsi.services.read.common import current_snapshot, market_lines


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
    market_games: int
    su_accuracy: float | None  # TSI favorite won (ties excluded)
    total_mae: float | None
    market_total_mae: float | None


@dataclass(frozen=True)
class ModelReport:
    season: int
    backtest: BacktestSummary | None
    live: LiveAccuracy
    versions: list[ModelVersion]


def model_report(session: Session, season: int, now: datetime) -> ModelReport:
    return ModelReport(
        season, _latest_backtest(session), _live(session, season, now), model_versions(session)
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


def _live(session: Session, season: int, now: datetime) -> LiveAccuracy:
    snaps = snapshots_for_season(session, season)
    games = [
        g
        for g in season_games(session, season, list(snaps))
        if g.completed and g.home_points is not None and g.start_time is not None
    ]
    closing = market_lines(session, games, now)
    errs, market_errs, su, tot_errs, market_tot = [], [], [], [], []
    for g in games:
        snap, locked = current_snapshot(snaps[g.id], g.start_time, now)
        if snap is None or not locked:
            continue
        margin, total = g.home_points - g.away_points, g.home_points + g.away_points
        errs.append(abs(-snap.spread - margin))
        tot_errs.append(abs(snap.total - total))
        if margin != 0 and snap.spread != 0:
            su.append((margin > 0) == (snap.spread < 0))
        line = closing.get(g.id)
        if line and line.spread is not None:
            market_errs.append(abs(-line.spread - margin))
        if line and line.total is not None:
            market_tot.append(abs(line.total - total))
    mean = lambda xs: sum(xs) / len(xs) if xs else None  # noqa: E731
    return LiveAccuracy(
        games=len(errs),
        mae=mean(errs),
        market_mae=mean(market_errs),
        market_games=len(market_errs),
        su_accuracy=mean([float(s) for s in su]),
        total_mae=mean(tot_errs),
        market_total_mae=mean(market_tot),
    )
