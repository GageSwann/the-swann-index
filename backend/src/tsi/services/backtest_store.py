"""Save a backtest run (config + metrics + report tables + git SHA) as a `model_runs` row
(kind='backtest'). The report tables feed `/model/report`."""

import subprocess
from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import ModelRun
from tsi.model.config import MODEL_VERSION
from tsi.services.backtest_result import BacktestResult
from tsi.services.report_export import Table


def current_git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip() or None


def save_backtest_run(
    session_factory: sessionmaker[Session],
    result: BacktestResult,
    through_season: int,
    report: dict[str, Table] | None = None,
) -> int:
    with session_factory.begin() as session:
        run = ModelRun(
            kind="backtest",
            season=through_season,
            week=0,
            season_type="regular",
            run_at=datetime.now(UTC),
            model_version=MODEL_VERSION,
            params={
                "config": result.config.to_dict(),
                "metrics": result.metrics(),
                "report": report or {},
            },
            git_sha=current_git_sha(),
        )
        session.add(run)
        session.flush()
        return run.id
