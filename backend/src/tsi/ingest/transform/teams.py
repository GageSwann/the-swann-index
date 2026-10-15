"""CFBD /teams?year= -> `teams` and `team_seasons` rows.

CFBD's `classification` (fbs/fcs/ii/iii) is our `division`. CFBD's own
`division` field is a conference sub-division (e.g. "East") and is ignored.
"""

import re
import unicodedata
from typing import Any

UNKNOWN_DIVISION = "unknown"


def slugify(school: str) -> str:
    """URL slug: 'Texas A&M' -> 'texas-am', "Hawai'i" -> 'hawaii', 'Miami (OH)' -> 'miami-oh'."""
    ascii_name = unicodedata.normalize("NFKD", school).encode("ascii", "ignore").decode()
    compact = re.sub(r"['&.]", "", ascii_name.lower())
    return re.sub(r"[^a-z0-9]+", "-", compact).strip("-")


def team_rows(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Stable identity rows. Slug collisions get the CFBD id appended."""
    rows = []
    used_slugs: set[str] = set()
    for team in sorted(raw, key=lambda t: t["id"]):  # deterministic collision handling
        slug = slugify(team["school"])
        if slug in used_slugs or not slug:
            slug = f"{slug}-{team['id']}".strip("-")
        used_slugs.add(slug)
        rows.append(
            {
                "id": team["id"],
                "school": team["school"],
                "slug": slug,
                "mascot": team.get("mascot"),
                "abbreviation": team.get("abbreviation"),
                "color": team.get("color"),
                "alt_color": team.get("alternateColor"),
                "logo_url": (team.get("logos") or [None])[0],
                "venue_id": (team.get("location") or {}).get("id"),
            }
        )
    return rows


def team_season_rows(raw: list[dict[str, Any]], season: int) -> list[dict[str, Any]]:
    return [
        {
            "team_id": team["id"],
            "season": season,
            "conference": team.get("conference"),
            "division": team.get("classification") or UNKNOWN_DIVISION,
        }
        for team in raw
    ]


def team_venues(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Venue objects embedded in team records (so teams.venue_id always has a target)."""
    return [team["location"] for team in raw if team.get("location")]
