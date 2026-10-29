"""ORM models, one module per area. Importing this package registers every table."""

from tsi.db.models.calendar import CalendarWeek
from tsi.db.models.games import Game, TeamGameStats
from tsi.db.models.ingest import IngestLog
from tsi.db.models.market import MarketLine
from tsi.db.models.predictions import Pick, Prediction
from tsi.db.models.ratings import ModelRun, Prior, TeamRating
from tsi.db.models.sim import SimResult
from tsi.db.models.teams import Team, TeamSeason, Venue

__all__ = [
    "CalendarWeek",
    "Game",
    "IngestLog",
    "MarketLine",
    "ModelRun",
    "Pick",
    "Prediction",
    "Prior",
    "SimResult",
    "Team",
    "TeamGameStats",
    "TeamRating",
    "TeamSeason",
    "Venue",
]
