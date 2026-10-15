"""Roster-change prior inputs: recruiting classes, transfer portal, head-coach changes.

All are preseason information for season Y (no look-ahead):
- recruiting: mean 247 class points over classes Y-3..Y (the current roster's recruits)
- portal: star-weighted transfers in minus out, entries dated before Aug 1 of Y,
  withdrawals excluded
- coach: the head coach in place before Aug 1 of Y (by hire date) vs. last year's
"""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from tsi.ingest.transform.timeutil import parse_utc

RECRUITING_CLASSES = 4
STAR_VALUE = {5: 3.0, 4: 2.0, 3: 1.0, 2: 0.5}
UNKNOWN_STAR_VALUE = 0.5
WITHDRAWN = "Withdrawn"


def preseason_cutoff(season: int) -> datetime:
    return datetime(season, 8, 1, tzinfo=UTC)


def recruiting_average(
    classes: Mapping[int, list[dict[str, Any]]], season: int, team_ids: Mapping[str, int]
) -> dict[int, float]:
    """`classes`: class year -> CFBD /recruiting/teams rows. Mean over available years."""
    totals: dict[int, list[float]] = {}
    for year in range(season - RECRUITING_CLASSES + 1, season + 1):
        for row in classes.get(year, []):
            team = team_ids.get(row.get("team"))
            if team is not None and row.get("points") is not None:
                totals.setdefault(team, []).append(float(row["points"]))
    return {team: sum(pts) / len(pts) for team, pts in totals.items()}


def portal_net(
    raw: list[dict[str, Any]], season: int, team_ids: Mapping[str, int]
) -> dict[int, float]:
    cutoff = preseason_cutoff(season)
    net: dict[int, float] = {}
    for move in raw:
        when = parse_utc(move.get("transferDate"))
        if move.get("eligibility") == WITHDRAWN or when is None or when >= cutoff:
            continue
        value = STAR_VALUE.get(move.get("stars"), UNKNOWN_STAR_VALUE)
        if (origin := team_ids.get(move.get("origin"))) is not None:
            net[origin] = net.get(origin, 0.0) - value
        if (dest := team_ids.get(move.get("destination"))) is not None:
            net[dest] = net.get(dest, 0.0) + value
    return net


def preseason_coaches(raw: list[dict[str, Any]], season: int) -> dict[int, int]:
    """team_id -> coach id of the most recently hired head coach before Aug 1 of `season`."""
    cutoff = preseason_cutoff(season)
    best: dict[int, tuple[datetime, int]] = {}
    for coach in raw:
        hired = parse_utc(coach.get("hireDate")) or datetime.min.replace(tzinfo=UTC)
        if hired >= cutoff:
            continue  # hired during/after this season: not the preseason coach
        for stint in coach.get("seasons") or []:
            if stint.get("year") == season and stint.get("teamId") is not None:
                team = stint["teamId"]
                if team not in best or hired > best[team][0]:
                    best[team] = (hired, coach["id"])
    return {team: coach_id for team, (_, coach_id) in best.items()}


def coach_changes(this_year: Mapping[int, int], last_year: Mapping[int, int]) -> dict[int, bool]:
    """True when the preseason head coach changed; only teams known in both years."""
    return {t: this_year[t] != last_year[t] for t in this_year.keys() & last_year.keys()}
