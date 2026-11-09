"""Pickle rankings + season projection at a fixed `now` (local DB) for before/after parity.

usage (from backend/): uv run python parity_snapshot.py OUT.pkl
"""

import pickle
import sys
from datetime import UTC, datetime

from sqlalchemy.orm import Session

import tsi  # noqa: F401
from tsi.config import get_settings
from tsi.db.engine import make_engine
from tsi.ingest.freshness import current_season
from tsi.model.artifact import production_artifact
from tsi.services.compute_rankings import build_rankings
from tsi.services.season_sim import project_season

NOW = datetime(2026, 11, 9, 19, 0, tzinfo=UTC)
artifact = production_artifact()
with Session(make_engine(get_settings())) as session:
    season = current_season(NOW)
    rankings = build_rankings(session, season, NOW, artifact.rating, artifact.sigma_season)
    projection = project_season(session, NOW, artifact)
with open(sys.argv[1], "wb") as f:
    pickle.dump({"rankings": repr(rankings), "projection": repr(projection)}, f)
print("saved", len(repr(rankings)), len(repr(projection)))
