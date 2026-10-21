"""Publish the board as immutable prediction snapshots (doc 05 §5, rule 2).

Each run inserts a NEW `predictions` row (and its picks) for every game whose
forecast, prices or picks changed since that game's latest snapshot; unchanged
games are skipped so re-runs don't pile up copies. Nothing is ever updated: the
DB trigger rejects it. The snapshot that counts for grading is the latest one
published before kickoff (the "locked" one).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import ModelRun, Pick, Prediction
from tsi.db.queries.calendar import calendar_week
from tsi.db.queries.predictions import (
    FINGERPRINT,
    PickKey,
    SnapshotKey,
    fingerprint,
    latest_snapshots,
)
from tsi.model.artifact import ModelArtifact
from tsi.services.backtest_store import current_git_sha
from tsi.services.board import BoardGame


@dataclass(frozen=True)
class PublishResult:
    run_id: int | None  # None when nothing changed
    published: int
    unchanged: int
    picks: int


def publish_board(
    session_factory: sessionmaker[Session],
    board: list[BoardGame],
    now: datetime,
    artifact: ModelArtifact,
) -> PublishResult:
    with session_factory.begin() as session:
        latest = latest_snapshots(session, [b.forecast.game.id for b in board])
        changed = [b for b in board if latest.get(b.forecast.game.id) != snapshot_key(b)]
        if not changed:
            return PublishResult(None, 0, len(board), 0)
        run = _new_run(session, changed, now, artifact)
        predictions = [Prediction(**prediction_row(b, run.id, now)) for b in changed]
        session.add_all(predictions)
        session.flush()
        picks = [
            Pick(**row)
            for b, p in zip(changed, predictions, strict=True)
            for row in pick_rows(b, p.id)
        ]
        session.add_all(picks)
        return PublishResult(run.id, len(changed), len(board) - len(changed), len(picks))


def prediction_row(b: BoardGame, run_id: int, now: datetime) -> dict[str, Any]:
    d, m = b.forecast.distribution, b.markets
    return {
        "run_id": run_id,
        "game_id": b.forecast.game.id,
        "variant": "raw",
        "published_at": now,
        "proj_home": d.home_points,
        "proj_away": d.away_points,
        "spread": m.fair_spread,
        "total": m.fair_total,
        "home_win_prob": d.home_win_prob,
        "sigma_margin": d.sigma_margin,
        "sigma_total": d.sigma_total,
        "rho": d.rho,
        "fair_home_ml": m.moneyline.first.fair,
        "fair_away_ml": m.moneyline.second.fair,
        "book_home_ml": m.moneyline.first.book,
        "book_away_ml": m.moneyline.second.book,
        "book_spread_home_odds": m.spread.first.book,
        "book_spread_away_odds": m.spread.second.book,
        "book_over_odds": m.total.first.book,
        "book_under_odds": m.total.second.book,
    }


def pick_rows(b: BoardGame, prediction_id: int) -> list[dict[str, Any]]:
    return [
        {
            "prediction_id": prediction_id,
            "market": p.market,
            "side": p.side,
            "line_taken": p.line,
            "odds_taken": p.odds,
            "edge": p.edge,
            "tier": p.tier,
            "stake_units": p.stake_units,
            "kelly_units": p.kelly_units,
        }
        for p in b.picks
    ]


def snapshot_key(b: BoardGame) -> SnapshotKey:
    row = prediction_row(b, 0, datetime.min)
    values = [row[col.key] for col in FINGERPRINT]
    picks = frozenset(PickKey(p.market, p.side, p.line, p.odds, p.tier) for p in b.picks)
    return SnapshotKey(fingerprint(values), picks)


def _new_run(
    session: Session, board: list[BoardGame], now: datetime, artifact: ModelArtifact
) -> ModelRun:
    game = board[0].forecast.game
    season_type, week = calendar_week(session, game.season, now)
    run = ModelRun(
        kind="live",
        season=game.season,
        week=week,
        season_type=season_type,
        run_at=now,
        model_version=artifact.version,
        params={
            "job": "publish",
            "fitted_seasons": list(artifact.fitted_seasons),
            "edge_shrink": [artifact.edge_shrink.k_spread, artifact.edge_shrink.k_total],
        },
        git_sha=current_git_sha(),
    )
    session.add(run)
    session.flush()
    return run
