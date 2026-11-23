"""Is the project on pace to go over Neon's free network transfer this period? (pure)

Neon's free plan allows 5 GB of network transfer a month for the whole project and
suspends the database over it (#140). The owner's target is half that pace, under
80 MB a day (#151). From the period's running total and how far into the period we are:
- `alert`: 80% of the limit used, or (after the first few days, so one heavy day early on
  can't trip it) on pace to pass the limit by the period's end;
- `above target`: averaging more than the target a day;
- `ok` otherwise.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from tsi.ops.neon_api import ProjectUsage

GB = 1_000_000_000  # Neon's console counts decimal units
MB = 1_000_000
FREE_LIMIT_BYTES = 5 * GB
TARGET_PER_DAY_BYTES = 80 * MB
ALERT_USED_SHARE = 0.8
MIN_DAYS_FOR_PACE = 3.0
MIN_DAY = 1.0  # elapsed time counts as at least a day (no blow-up just after a reset)

OK, ABOVE_TARGET, ALERT = "ok", "above target", "alert"


@dataclass(frozen=True)
class TransferReading:
    used_bytes: int
    period_start: datetime
    period_end: datetime
    period_source: str  # "neon" or "calendar month" (Neon's dates didn't bracket now)
    days_elapsed: float
    days_in_period: float
    per_day_bytes: float
    projected_bytes: float  # at today's average pace, by the period's end
    limit_bytes: int
    status: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "used_bytes": self.used_bytes,
            "per_day_bytes": round(self.per_day_bytes),
            "projected_bytes": round(self.projected_bytes),
            "limit_bytes": self.limit_bytes,
            "days_elapsed": round(self.days_elapsed, 2),
            "days_in_period": round(self.days_in_period, 2),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "period_source": self.period_source,
        }


def assess(
    usage: ProjectUsage,
    now: datetime,
    limit_bytes: int = FREE_LIMIT_BYTES,
    target_per_day_bytes: int = TARGET_PER_DAY_BYTES,
) -> TransferReading:
    start, end, source = _period(usage, now)
    days_in_period = (end - start) / timedelta(days=1)
    days_elapsed = (now - start) / timedelta(days=1)
    per_day = usage.transfer_bytes / max(days_elapsed, MIN_DAY)
    projected = per_day * days_in_period
    used = usage.transfer_bytes
    if used >= ALERT_USED_SHARE * limit_bytes:
        status, reason = (
            ALERT,
            f"{_gb(used)} used, over {ALERT_USED_SHARE:.0%} of {_gb(limit_bytes)}",
        )
    elif days_elapsed >= MIN_DAYS_FOR_PACE and projected > limit_bytes:
        status, reason = (
            ALERT,
            f"on pace for {_gb(projected)} by {end:%b} {end.day}, over {_gb(limit_bytes)}",
        )
    elif per_day > target_per_day_bytes:
        status, reason = (
            ABOVE_TARGET,
            (f"averaging {_mb(per_day)} a day, above the {_mb(target_per_day_bytes)} target"),
        )
    else:
        status, reason = OK, f"averaging {_mb(per_day)} a day"
    return TransferReading(
        used_bytes=used,
        period_start=start,
        period_end=end,
        period_source=source,
        days_elapsed=days_elapsed,
        days_in_period=days_in_period,
        per_day_bytes=per_day,
        projected_bytes=projected,
        limit_bytes=limit_bytes,
        status=status,
        reason=reason,
    )


def describe(r: TransferReading) -> str:
    return (
        f"Neon transfer {r.status}: {r.reason}. {_gb(r.used_bytes)} used in "
        f"{r.days_elapsed:.1f} of {r.days_in_period:.1f} days "
        f"({r.period_start:%b %d} - {r.period_end:%b %d} UTC, {r.period_source}); "
        f"pace {_gb(r.projected_bytes)} by the end, limit {_gb(r.limit_bytes)}."
    )


def _period(usage: ProjectUsage, now: datetime) -> tuple[datetime, datetime, str]:
    """Neon's consumption period when it brackets now; else the calendar month (UTC)."""
    start, end = usage.period_start, usage.period_end
    if start and end and start <= now < end and end - start >= timedelta(days=1):
        return start, end, "neon"
    month = datetime(now.year, now.month, 1, tzinfo=UTC)
    following = datetime(now.year + now.month // 12, now.month % 12 + 1, 1, tzinfo=UTC)
    return month, following, "calendar month"


def _gb(n: float) -> str:
    return f"{n / GB:.2f} GB"


def _mb(n: float) -> str:
    return f"{n / MB:.0f} MB"
