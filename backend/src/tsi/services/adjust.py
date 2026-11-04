"""Add, list and expire manual adjustments (`tsi adjust`, decision #103).

Adjustments are the operator's judgment (injuries, QB changes) layered on top of the
model; the model itself never reads them. Rows are never edited after the fact except
to close their window early (`expire`), and never deleted.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import Adjustment
from tsi.db.queries.adjustments import StoredAdjustment, season_adjustments
from tsi.db.queries.team_info import team_id_by_slug
from tsi.ingest.freshness import current_season

MAX_POINTS = 21.0  # per side; anything bigger is almost surely a typo


class AdjustmentError(ValueError):
    """A request the operator should fix (unknown team, zero points, bad window)."""


@dataclass(frozen=True)
class NewAdjustment:
    team_slug: str
    off_points: float
    def_points: float
    reason: str
    starts_at: datetime | None = None  # default: now
    ends_at: datetime | None = None  # default: rest of the season


def add_adjustment(sessions: sessionmaker[Session], new: NewAdjustment, now: datetime) -> int:
    """Validate and insert one adjustment; returns its id."""
    _check_points(new.off_points, new.def_points)
    reason = new.reason.strip()
    if not reason:
        raise AdjustmentError("Give a reason (it is shown next to the adjusted numbers).")
    starts_at = new.starts_at or now
    if new.ends_at is not None and new.ends_at <= starts_at:
        raise AdjustmentError("The end must be after the start.")
    if new.ends_at is not None and new.ends_at <= now:
        raise AdjustmentError("That window has already ended.")

    with sessions.begin() as session:
        team_id = team_id_by_slug(session, new.team_slug)
        if team_id is None:
            raise AdjustmentError(f"No team with slug '{new.team_slug}'.")
        row = Adjustment(
            season=current_season(now),
            team_id=team_id,
            off_points=new.off_points,
            def_points=new.def_points,
            reason=reason,
            starts_at=starts_at,
            ends_at=new.ends_at,
        )
        session.add(row)
        session.flush()
        return row.id


def list_adjustments(
    session: Session, now: datetime, *, include_ended: bool = False, season: int | None = None
) -> list[StoredAdjustment]:
    """This season's adjustments whose window is still open (or all of them)."""
    return season_adjustments(
        session, season or current_season(now), open_at=None if include_ended else now
    )


def expire_adjustment(sessions: sessionmaker[Session], adjustment_id: int, now: datetime) -> None:
    """Close the window now: games from here on are no longer adjusted. Past ones keep it."""
    with sessions.begin() as session:
        row = session.get(Adjustment, adjustment_id)
        if row is None:
            raise AdjustmentError(f"No adjustment #{adjustment_id}.")
        if row.ends_at is not None and row.ends_at <= now:
            raise AdjustmentError(f"Adjustment #{adjustment_id} has already ended.")
        row.ends_at = max(now, row.starts_at)
        row.expired_at = now


def _check_points(off: float, defense: float) -> None:
    if off == 0 and defense == 0:
        raise AdjustmentError("Give --off and/or --def points (both are zero).")
    for side, value in (("--off", off), ("--def", defense)):
        if abs(value) > MAX_POINTS:
            raise AdjustmentError(f"{side} {value:+g} is beyond ±{MAX_POINTS:g} points.")
