"""Call ledger: records every CFBD request and counts this month's real API calls.

The client depends on the `CallLedger` protocol, so tests can use an in-memory
fake; `DbCallLedger` is the real implementation backed by `ingest_log`.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import IngestLog


@dataclass(frozen=True)
class CallRecord:
    endpoint: str
    params: dict[str, Any]
    fetched_at: datetime
    from_cache: bool
    status: str  # "ok" | "error"
    row_count: int | None = None


class CallLedger(Protocol):
    def calls_this_month(self, now: datetime) -> int: ...

    def record(self, entry: CallRecord) -> None: ...


def month_start(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


class DbCallLedger:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def calls_this_month(self, now: datetime) -> int:
        query = (
            select(func.count())
            .select_from(IngestLog)
            .where(IngestLog.from_cache.is_(False), IngestLog.fetched_at >= month_start(now))
        )
        with self._session_factory() as session:
            return session.scalar(query) or 0

    def record(self, entry: CallRecord) -> None:
        with self._session_factory.begin() as session:
            session.add(
                IngestLog(
                    endpoint=entry.endpoint,
                    params=entry.params,
                    season=_as_int(entry.params.get("year")),
                    week=_as_int(entry.params.get("week")),
                    fetched_at=entry.fetched_at,
                    from_cache=entry.from_cache,
                    row_count=entry.row_count,
                    status=entry.status,
                )
            )


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
