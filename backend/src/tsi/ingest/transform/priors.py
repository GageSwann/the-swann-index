"""CFBD /talent and /player/returning -> partial `priors` rows (preseason inputs).

Both are published before the season, so using them for season Y's prior is not
look-ahead. Each source fills only its own column; the other columns are untouched.
- talent: 247Sports team talent composite
- returning_ppa: share (0-1) of last season's offensive PPA that returns (`percentPPA`)
- returning_passing_ppa: the same for passing only (`percentPassingPPA`; QB continuity)
"""

from collections.abc import Mapping
from typing import Any

from tsi.ingest.convert import to_float


def talent_rows(
    raw: list[dict[str, Any]], season: int, team_ids: Mapping[str, int]
) -> list[dict[str, Any]]:
    return [
        {"season": season, "team_id": team_ids[r["team"]], "talent": float(r["talent"])}
        for r in raw
        if r.get("team") in team_ids and r.get("talent") is not None
    ]


def returning_rows(
    raw: list[dict[str, Any]], season: int, team_ids: Mapping[str, int]
) -> list[dict[str, Any]]:
    return [
        {
            "season": season,
            "team_id": team_ids[r["team"]],
            "returning_ppa": float(r["percentPPA"]),
            "returning_passing_ppa": to_float(r.get("percentPassingPPA")),
        }
        for r in raw
        if r.get("team") in team_ids and r.get("percentPPA") is not None
    ]
