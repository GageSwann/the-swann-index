"""CFBD /stats/game/advanced -> `team_game_stats` rows (one per team per game: its offense).

Two versions of the same endpoint are combined:
- garbage-time EXCLUDED -> efficiency (EPA/play, success rate, explosiveness, rush/pass EPA)
- full game              -> plays and drives, so points-per-drive matches full-game points

CFBD identifies teams by school name; `game_index` maps each game's two school
names to (team_id, points) from our `games` table. A team's defense for a game is
its opponent's row (verified: CFBD's defense block equals the opponent's offense).
"""

from collections.abc import Mapping
from typing import Any

# game_id -> school name -> (team_id, points scored in that game)
GameIndex = Mapping[int, Mapping[str, tuple[int, int | None]]]


def team_game_stat_rows(
    filtered: list[dict[str, Any]],
    full: list[dict[str, Any]],
    game_index: GameIndex,
) -> list[dict[str, Any]]:
    full_offense = {(r["gameId"], r["team"]): r["offense"] for r in full}
    rows: dict[tuple[int, int], dict[str, Any]] = {}
    for record in filtered:
        game_id, school = record["gameId"], record["team"]
        match = game_index.get(game_id, {}).get(school)
        if match is None:
            continue  # game not loaded or unknown school; reported by the loader
        team_id, points = match
        offense = record["offense"]
        whole = full_offense.get((game_id, school), {})
        rows[(game_id, team_id)] = {
            "game_id": game_id,
            "team_id": team_id,
            "points": points,
            "plays": whole.get("plays"),
            "drives": whole.get("drives"),
            "epa_per_play": offense.get("ppa"),
            "rush_epa_per_play": (offense.get("rushingPlays") or {}).get("ppa"),
            "pass_epa_per_play": (offense.get("passingPlays") or {}).get("ppa"),
            "success_rate": offense.get("successRate"),
            "explosiveness": offense.get("explosiveness"),
            "garbage_time_filtered": True,
        }
    return list(rows.values())
