"""Idempotent bulk upsert (Postgres INSERT ... ON CONFLICT) keyed on the primary key.

Rows are sent as one executemany (SQLAlchemy "insertmanyvalues": the statement is
compiled once and batched), which is ~3-4x faster than building a giant VALUES
literal. On conflict, a row is only rewritten if some value actually changed, so
the nightly re-load of an unchanged season writes almost nothing.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from tsi.db.base import Base

NEVER_UPDATED = {"created_at"}


def upsert_rows(
    session: Session,
    model: type[Base],
    rows: Sequence[Mapping[str, Any]],
    *,
    update: bool = True,
) -> int:
    """Insert rows; on primary-key conflict update changed non-key columns.

    `update=False` keeps existing rows untouched. All rows must share the same keys.
    Returns the number of rows sent.
    """
    if not rows:
        return 0
    table = model.__table__
    key_cols = [col.name for col in table.primary_key.columns]
    update_cols = [c for c in rows[0] if c not in key_cols and c not in NEVER_UPDATED]

    stmt = insert(table)
    if update and update_cols:
        changed = or_(*(table.c[c].is_distinct_from(stmt.excluded[c]) for c in update_cols))
        stmt = stmt.on_conflict_do_update(
            index_elements=key_cols,
            set_={c: stmt.excluded[c] for c in update_cols},
            where=changed,
        )
    else:
        stmt = stmt.on_conflict_do_nothing(index_elements=key_cols)
    session.execute(stmt, list(rows))
    return len(rows)
