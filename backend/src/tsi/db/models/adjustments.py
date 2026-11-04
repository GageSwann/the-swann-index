"""Manual adjustments (doc 04 §11, decision #103): the operator's ± points on top of the model.

Kept apart from the model's own ratings (rule 6), so raw and adjusted can always be
shown side by side. An adjustment covers the team's games that kick off inside
[starts_at, ends_at) (open-ended when `ends_at` is None) in its season.

Rows are never deleted: `tsi adjust expire` closes the window (`ends_at`) and stamps
`expired_at`, so a published snapshot can always be traced to the adjustments that
existed when it was made (`created_at` / `expired_at`).
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from tsi.db.base import Base, CreatedAtMixin


class Adjustment(CreatedAtMixin, Base):
    __tablename__ = "adjustments"
    __table_args__ = (
        CheckConstraint("off_points <> 0 OR def_points <> 0", name="nonzero"),
        CheckConstraint("ends_at IS NULL OR ends_at >= starts_at", name="window"),
        Index("ix_adjustments_season_team", "season", "team_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    season: Mapped[int]
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    # Points per game vs. the model: offense = points the team scores, defense = points it
    # keeps off the board. Net rating change = off + def (e.g. QB out: off -4, def 0).
    off_points: Mapped[float] = mapped_column(server_default="0")
    def_points: Mapped[float] = mapped_column(server_default="0")
    reason: Mapped[str]
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime | None]
    expired_at: Mapped[datetime | None]  # set by `tsi adjust expire`
