"""Team display names."""

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import Team


def team_names(session: Session, team_ids: Iterable[int] | None = None) -> dict[int, str]:
    query = select(Team.id, Team.school)
    if team_ids is not None:
        query = query.where(Team.id.in_(list(team_ids)))
    return {tid: school for tid, school in session.execute(query)}
