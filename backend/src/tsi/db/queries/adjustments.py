"""Manual adjustments with their team names."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from tsi.db.models import Adjustment, Team
from tsi.db.queries.filters import one_of


@dataclass(frozen=True)
class StoredAdjustment:
    id: int
    season: int
    team_id: int
    school: str
    off_points: float
    def_points: float
    reason: str
    starts_at: datetime
    ends_at: datetime | None
    created_at: datetime
    expired_at: datetime | None

    @property
    def points(self) -> float:
        """Net change to the team's rating (margin points per game)."""
        return self.off_points + self.def_points

    def covers(self, kickoff: datetime) -> bool:
        """Does the window include a game kicking off at `kickoff`?"""
        return self.starts_at <= kickoff and (self.ends_at is None or kickoff < self.ends_at)


def season_adjustments(
    session: Session, season: int, *, open_at: datetime | None = None
) -> list[StoredAdjustment]:
    """The season's adjustments, oldest first; with `open_at`, only windows still open then."""
    query = _query().where(Adjustment.season == season)
    if open_at is not None:
        query = query.where(or_(Adjustment.ends_at.is_(None), Adjustment.ends_at > open_at))
    return [StoredAdjustment(*row) for row in session.execute(query)]


def adjustments_by_id(session: Session, ids: Iterable[int]) -> dict[int, StoredAdjustment]:
    ids = set(ids)
    if not ids:
        return {}
    return {
        row[0]: StoredAdjustment(*row)
        for row in session.execute(_query().where(one_of(Adjustment.id, ids)))
    }


def _query() -> Select:
    return (
        select(
            Adjustment.id,
            Adjustment.season,
            Adjustment.team_id,
            Team.school,
            Adjustment.off_points,
            Adjustment.def_points,
            Adjustment.reason,
            Adjustment.starts_at,
            Adjustment.ends_at,
            Adjustment.created_at,
            Adjustment.expired_at,
        )
        .join(Team, Team.id == Adjustment.team_id)
        .order_by(Adjustment.id)
    )
