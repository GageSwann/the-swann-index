"""Idempotent bulk upsert (Postgres INSERT ... ON CONFLICT) keyed on the primary key."""

from collections.abc import Iterable, Mapping
from itertools import batched
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from tsi.db.base import Base

CHUNK_SIZE = 1000  # well under Postgres's 65,535 bind-parameter limit
NEVER_UPDATED = {"created_at"}


def upsert_rows(
    session: Session,
    model: type[Base],
    rows: Iterable[Mapping[str, Any]],
    *,
    update: bool = True,
) -> int:
    """Insert rows; on primary-key conflict update non-key columns (or skip if `update=False`).

    Re-running with the same rows never creates duplicates. Returns rows sent.
    """
    table = model.__table__
    key_cols = [col.name for col in table.primary_key.columns]
    sent = 0
    for chunk in batched(rows, CHUNK_SIZE):
        stmt = insert(table).values(list(chunk))
        update_cols = {
            name: stmt.excluded[name]
            for name in chunk[0]
            if name not in key_cols and name not in NEVER_UPDATED
        }
        if update and update_cols:
            stmt = stmt.on_conflict_do_update(index_elements=key_cols, set_=update_cols)
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=key_cols)
        session.execute(stmt)
        sent += len(chunk)
    return sent
