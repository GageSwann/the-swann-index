"""Team display names."""

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import Team
from tsi.db.queries.filters import one_of


def team_names(session: Session, team_ids: Iterable[int] | None = None) -> dict[int, str]:
    query = select(Team.id, Team.school)
    if team_ids is not None:
        query = query.where(one_of(Team.id, team_ids))
    return {tid: school for tid, school in session.execute(query)}
