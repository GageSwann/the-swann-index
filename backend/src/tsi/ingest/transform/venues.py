"""CFBD venue objects (from /venues, or a team's `location`) -> `venues` rows."""

from typing import Any

from tsi.ingest.convert import to_float


def venue_row(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Row for one venue, or None when CFBD gives an empty placeholder (no id)."""
    if raw.get("id") is None:
        return None
    return {
        "id": raw["id"],
        "name": raw.get("name") or f"Venue {raw['id']}",
        "city": raw.get("city"),
        "state": raw.get("state"),
        "latitude": raw.get("latitude"),
        "longitude": raw.get("longitude"),
        "elevation_m": to_float(raw.get("elevation")),  # CFBD sends meters as a string
        "dome": raw.get("dome"),
    }


def venue_rows(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = {}
    for item in raw:
        row = venue_row(item)
        if row is not None:
            rows[row["id"]] = row  # de-duplicate by id; last one wins
    return list(rows.values())
