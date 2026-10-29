"""Shared WHERE helpers."""

from collections.abc import Iterable

from sqlalchemy import ARRAY, ColumnElement, any_, literal
from sqlalchemy.orm import InstrumentedAttribute


def one_of[T](column: InstrumentedAttribute[T], values: Iterable[T]) -> ColumnElement[bool]:
    """`column = ANY(:values)`: one array parameter instead of an `IN` list.

    The SQL text stays the same whatever the number of values, so SQLAlchemy reuses the
    compiled statement and psycopg doesn't re-parse a long list each time (the week board
    sends hundreds of game ids). An empty list matches nothing, like an empty `IN`.
    """
    return column == any_(literal(list(values), ARRAY(column.type)))
