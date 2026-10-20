"""Export the backtest, Book backtest, SP+ check, and model weights as report tables."""

import csv
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from tsi.backtest.calibration import CalibrationBin
from tsi.backtest.evaluate import Summary
from tsi.ingest.client import CfbdClient
from tsi.model.artifact import ModelArtifact
from tsi.model.stack import BUCKET_EDGES, FEATURES
from tsi.services.backtest import BacktestResult, ComparisonRow
from tsi.services.book_backtest import BookBacktest
from tsi.services.sp_check import compare_with_sp

Table = list[dict[str, Any]]
BOOK_PERIODS = {"Train": "Train 2021–22", "Validate": "Validate 2023–25"}  # openers: 2021+
PERIOD_LABELS = {
    "Train": "Train 2015–22",
    "Validate": "Validate 2023–25",
    "both teams 4+ games": "Validate: both teams 4+ games",
    "provisional (<4)": "Validate: early season (<4 games)",
}


def _accuracy(row: ComparisonRow) -> dict[str, Any]:
    p: Summary = row.predictive
    return {
        "games": p.games,
        "season_mae": round(row.season.mae, 3),
        "predictive_mae": round(p.mae, 3),
        "elo_mae": round(row.elo.mae, 3),
        "vegas_mae": round(p.market_mae, 3),
        "predictive_su": round(p.su_accuracy, 4),
        "elo_su": round(row.elo.su_accuracy, 4),
        "vegas_su": round(p.market_su_accuracy, 4),
        "predictive_brier": round(p.brier, 4),
    }


def by_season(result: BacktestResult) -> Table:
    return [
        {"season": int(r.season.label), **_accuracy(r)}
        for r in result.rows
        if r.season.label.isdigit()
    ]


def periods(result: BacktestResult) -> Table:
    out = []
    for r in result.rows:
        label = r.season.label.strip()
        key = next((k for k in PERIOD_LABELS if label.startswith(k)), None)
        if key:
            out.append({"period": PERIOD_LABELS[key], **_accuracy(r)})
    return out


def calibration(result: BacktestResult) -> Table:
    return _bins(result.calibration)


def book_calibration(result: BacktestResult) -> Table:
    """The Book's shrunk P(home covers) / P(over) at the opener, validation seasons."""
    return [
        {"market": market, **row}
        for market, bins in (("spread", result.lines.cover), ("total", result.lines.over))
        for row in _bins(bins)
    ]


def book_record(book: BookBacktest) -> Table:
    """Book record by period/season, market and star tier (tier 0 = all tiers)."""
    return [
        {
            "period": BOOK_PERIODS.get(r.label.split(" ")[0], r.label),
            "market": r.market,
            "tier": r.tier,
            "bets": r.bets,
            "wins": r.wins,
            "losses": r.losses,
            "pushes": r.pushes,
            "win_rate": round(r.win_rate, 4),
            "units": round(r.units, 2),
            "roi": round(r.roi, 4),
            "kelly_units": round(r.kelly_units, 2),
            "clv": None if r.clv is None else round(r.clv, 3),
            "beat_close": None if r.beat_close is None else round(r.beat_close, 4),
        }
        for r in book.records
    ]


def book_bets(book: BookBacktest) -> Table:
    """Every simulated Book bet, in kickoff order (for the cumulative-units chart)."""
    bets = sorted(book.bets, key=lambda b: (b.kickoff is None, b.kickoff))
    return [
        {
            "date": b.kickoff.date().isoformat() if b.kickoff else "",
            "season": b.season,
            "market": b.market,
            "side": b.side,
            "tier": b.tier,
            "result": b.result,
            "units": round(b.units, 4),
            "kelly_units": round(b.kelly_units, 4),
            "clv": None if b.clv is None else round(b.clv, 2),
        }
        for b in bets
    ]


def totals_accuracy(result: BacktestResult) -> Table:
    return [
        {
            "period": PERIOD_LABELS.get(t.label.split(" ")[0], t.label),
            "games": t.games,
            "tsi_mae": round(t.mae, 3),
            "vegas_mae": round(t.market_mae, 3),
            "bias": round(t.bias, 3),
            "ou_vs_close": round(t.ou_accuracy, 4),
        }
        for t in result.totals
    ]


def _bins(bins: list[CalibrationBin]) -> Table:
    return [
        {
            "bin": f"{100 * b.low:.0f}–{100 * b.high:.0f}%",
            "games": b.games,
            "predicted": round(b.predicted, 4),
            "observed": round(b.observed, 4),
        }
        for b in bins
    ]


def ats(result: BacktestResult) -> Table:
    return [
        {
            "min_edge": a.min_edge,
            "bets": a.bets,
            "wins": a.wins,
            "losses": a.losses,
            "pushes": a.pushes,
            "win_rate": round(a.win_rate, 4),
        }
        for a in result.ats
    ]


def stack_weights(artifact: ModelArtifact) -> Table:
    edges = (*BUCKET_EDGES, None)
    rows = []
    for bucket, coef in sorted(artifact.stack.coefs.items()):
        low, high = edges[bucket], edges[bucket + 1]
        stage = (
            f"{low}+" if high is None else (f"{low}" if high - low == 1 else f"{low}–{high - 1}")
        )
        for feature, weight in zip(FEATURES, coef, strict=True):
            rows.append(
                {
                    "stage": stage,
                    "min_games": low,
                    "feature": feature,
                    "weight": round(float(weight), 4),
                }
            )
    return rows


def sp_agreement(client: CfbdClient, session: Session, first: int, last: int) -> Table:
    return [
        {
            "season": r.season,
            "teams": r.agreement.teams,
            "pearson": round(r.agreement.pearson, 4),
            "spearman": round(r.agreement.spearman, 4),
        }
        for r in compare_with_sp(client, session, range(first, last + 1))
    ]


def write_csv(rows: Table, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
