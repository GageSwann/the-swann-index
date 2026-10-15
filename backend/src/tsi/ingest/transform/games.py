"""CFBD /games?year=&seasonType=both -> `games` rows, plus team rows for unknown opponents.

CFBD /games includes opponents missing from /teams (mostly NAIA). They get a
minimal placeholder team (slug suffixed with the CFBD id, so it can never collide
with a real team's slug) and a team_season built from the game record.
"""

from typing import Any

from tsi.ingest.transform.calendar import SEASON_TYPES
from tsi.ingest.transform.teams import UNKNOWN_DIVISION, slugify
from tsi.ingest.transform.timeutil import parse_utc

SIDES = ("home", "away")


def relevant_games(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Regular season and postseason only (drops all-star/spring games), one per id.

    De-duplicating matters: a repeated id in one upsert batch makes Postgres fail.
    """
    by_id = {g["id"]: g for g in raw if g.get("seasonType") in SEASON_TYPES}
    return list(by_id.values())


def game_rows(
    raw: list[dict[str, Any]], known_venues: set[int] | None = None
) -> list[dict[str, Any]]:
    """Game rows. A venue id not in `known_venues` becomes None (venues list may lag)."""
    rows = [
        {
            "id": g["id"],
            "season": g["season"],
            "week": g["week"],
            "season_type": g["seasonType"],
            "start_time": parse_utc(g.get("startDate")),
            "start_time_tbd": bool(g.get("startTimeTBD")),
            "home_id": g["homeId"],
            "away_id": g["awayId"],
            "venue_id": g.get("venueId"),
            "neutral_site": bool(g.get("neutralSite")),
            "conference_game": bool(g.get("conferenceGame")),
            "home_points": g.get("homePoints"),
            "away_points": g.get("awayPoints"),
            "completed": bool(g.get("completed")),
            "notes": g.get("notes") or None,
        }
        for g in relevant_games(raw)
    ]
    if known_venues is not None:
        for row in rows:
            if row["venue_id"] not in known_venues:
                row["venue_id"] = None
    return rows


def participant_team_seasons(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Season membership as seen in game records (used only to fill gaps)."""
    rows: dict[tuple[int, int], dict[str, Any]] = {}
    for g in relevant_games(raw):
        for side in SIDES:
            key = (g[f"{side}Id"], g["season"])
            rows.setdefault(
                key,
                {
                    "team_id": key[0],
                    "season": key[1],
                    "conference": g.get(f"{side}Conference"),
                    "division": g.get(f"{side}Classification") or UNKNOWN_DIVISION,
                },
            )
    return list(rows.values())


def placeholder_teams(raw: list[dict[str, Any]], known_ids: set[int]) -> list[dict[str, Any]]:
    """Minimal team rows for game participants not already in `teams`."""
    rows: dict[int, dict[str, Any]] = {}
    for g in relevant_games(raw):
        for side in SIDES:
            team_id, name = g[f"{side}Id"], g[f"{side}Team"]
            if team_id not in known_ids and team_id not in rows:
                rows[team_id] = {
                    "id": team_id,
                    "school": name,
                    "slug": f"{slugify(name)}-{team_id}",
                }
    return list(rows.values())
