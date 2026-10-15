"""CFBD /lines -> `market_lines` snapshots, stored only when a provider's numbers change.

Sign convention (verified on 2024: 0 mismatches vs. CFBD's formattedSpread):
`spread` is from the HOME team's view, negative = home favored. Same as ours.

History rules, per (game, provider):
- Insert a new row only if its values differ from the latest stored row.
- A row captured at/after kickoff is the close (`is_closing`). If values didn't
  change, the latest stored row is marked closing instead of adding a duplicate.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

VALUE_FIELDS = ("spread", "spread_open", "total", "total_open", "home_ml", "away_ml")
LineKey = tuple[int, str]  # (game_id, provider)


@dataclass(frozen=True)
class StoredLine:
    id: int
    values: tuple[Any, ...]
    is_closing: bool


@dataclass
class LinePlan:
    inserts: list[dict[str, Any]] = field(default_factory=list)
    mark_closing: list[int] = field(default_factory=list)  # existing row ids


def line_snapshots(raw: list[dict[str, Any]]) -> dict[LineKey, dict[str, Any]]:
    """One snapshot per (game, provider); providers with no numbers at all are skipped."""
    snapshots: dict[LineKey, dict[str, Any]] = {}
    for game in raw:
        for line in game.get("lines") or []:
            row = {
                "game_id": game["id"],
                "provider": line["provider"],
                "spread": _num(line.get("spread")),
                "spread_open": _num(line.get("spreadOpen")),
                "total": _num(line.get("overUnder")),
                "total_open": _num(line.get("overUnderOpen")),
                "home_ml": _int(line.get("homeMoneyline")),
                "away_ml": _int(line.get("awayMoneyline")),
            }
            if any(row[f] is not None for f in VALUE_FIELDS):
                snapshots[(row["game_id"], row["provider"])] = row
    return snapshots


def plan_line_changes(
    snapshots: Mapping[LineKey, dict[str, Any]],
    latest: Mapping[LineKey, StoredLine],
    kickoff: Mapping[int, datetime | None],
    fetched_at: datetime,
) -> LinePlan:
    plan = LinePlan()
    for key, snap in snapshots.items():
        if key[0] not in kickoff:
            continue  # game not in our games table
        start = kickoff[key[0]]
        after_kickoff = start is not None and fetched_at >= start
        stored = latest.get(key)
        values = tuple(snap[f] for f in VALUE_FIELDS)
        if stored is None or stored.values != values:
            plan.inserts.append({**snap, "fetched_at": fetched_at, "is_closing": after_kickoff})
        elif after_kickoff and not stored.is_closing:
            plan.mark_closing.append(stored.id)
    return plan


def _num(value: Any) -> float | None:
    return None if value is None else float(value)


def _int(value: Any) -> int | None:
    return None if value is None else int(value)
