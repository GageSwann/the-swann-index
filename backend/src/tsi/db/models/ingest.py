"""Log of every real CFBD request (not cache hits): powers the monthly call budget."""

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from tsi.db.base import Base, CreatedAtMixin


class IngestLog(CreatedAtMixin, Base):
    __tablename__ = "ingest_log"
    __table_args__ = (CheckConstraint("status IN ('ok', 'error')", name="status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint: Mapped[str] = mapped_column(index=True)
    params: Mapped[dict[str, Any]]  # query params only; never auth headers
    season: Mapped[int | None]
    week: Mapped[int | None]
    fetched_at: Mapped[datetime] = mapped_column(index=True)
    row_count: Mapped[int | None]
    status: Mapped[str]
