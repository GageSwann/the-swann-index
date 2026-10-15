"""CFBD /calendar?year= -> `calendar_weeks` rows."""

from typing import Any

from tsi.ingest.transform.timeutil import parse_utc

SEASON_TYPES = {"regular", "postseason"}


def calendar_rows(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "season": week["season"],
            "season_type": week["seasonType"],
            "week": week["week"],
            "start_date": parse_utc(week["startDate"]),
            "end_date": parse_utc(week["endDate"]),
        }
        for week in raw
        if week.get("seasonType") in SEASON_TYPES
    ]
