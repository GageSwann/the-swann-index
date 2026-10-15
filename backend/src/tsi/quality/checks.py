"""The data quality rules (doc 03).

Each check is a SQL query returning one row per problem: (season, detail).
`fail` rules guard correctness (look-ahead, integrity, FBS data the model needs);
`warn` rules flag known source gaps the model must tolerate. Every query takes
`:season` (NULL = all seasons).
"""

from dataclasses import dataclass
from typing import Literal

Severity = Literal["fail", "warn"]

SEASON_FILTER = "(CAST(:season AS integer) IS NULL OR g.season = CAST(:season AS integer))"

# Games with each side's division for that season.
GAMES = f"""
  SELECT g.*, hs.division AS home_div, aws.division AS away_div,
         h.school AS home_school, a.school AS away_school
  FROM games g
  JOIN teams h ON h.id = g.home_id
  JOIN teams a ON a.id = g.away_id
  LEFT JOIN team_seasons hs ON hs.team_id = g.home_id AND hs.season = g.season
  LEFT JOIN team_seasons aws ON aws.team_id = g.away_id AND aws.season = g.season
  WHERE {SEASON_FILTER}
"""
FBS_INVOLVED = "(home_div = 'fbs' OR away_div = 'fbs')"
FBS_VS_FBS = "(home_div = 'fbs' AND away_div = 'fbs')"
MATCHUP = "x.home_school || ' vs ' || x.away_school || ' (game ' || x.id || ')'"


@dataclass(frozen=True)
class Check:
    name: str
    severity: Severity
    description: str
    sql: str


CHECKS: tuple[Check, ...] = (
    # --- Look-ahead guards ---------------------------------------------------
    Check(
        "completed_game_in_future",
        "fail",
        "Completed game with a kickoff time in the future",
        f"SELECT x.season, {MATCHUP} FROM ({GAMES}) x WHERE completed AND start_time > now()",
    ),
    Check(
        "stats_on_unplayed_game",
        "fail",
        "Team stats exist for a game that isn't completed",
        f"""SELECT x.season, {MATCHUP} FROM ({GAMES}) x WHERE NOT completed
            AND EXISTS (SELECT 1 FROM team_game_stats s WHERE s.game_id = x.id)""",
    ),
    Check(
        "closing_line_before_kickoff",
        "fail",
        "A line marked closing was captured before kickoff",
        f"""SELECT x.season, {MATCHUP} || ' ' || m.provider FROM ({GAMES}) x
            JOIN market_lines m ON m.game_id = x.id
            WHERE m.is_closing AND m.fetched_at < x.start_time""",
    ),
    # --- Integrity ----------------------------------------------------------
    Check(
        "participant_missing_team_season",
        "fail",
        "A game's team has no conference/division row for that season",
        f"SELECT x.season, {MATCHUP} FROM ({GAMES}) x WHERE home_div IS NULL OR away_div IS NULL",
    ),
    Check(
        "stats_points_mismatch",
        "fail",
        "Points in team_game_stats differ from the game score",
        f"""SELECT x.season, {MATCHUP} FROM ({GAMES}) x JOIN team_game_stats s ON s.game_id = x.id
            WHERE s.points IS DISTINCT FROM
                  CASE WHEN s.team_id = x.home_id THEN x.home_points ELSE x.away_points END""",
    ),
    Check(
        "fbs_stats_one_side_only",
        "fail",
        "FBS game has stats for only one team",
        f"""SELECT x.season, {MATCHUP} FROM ({GAMES}) x WHERE {FBS_INVOLVED}
            AND (SELECT count(*) FROM team_game_stats s WHERE s.game_id = x.id) = 1""",
    ),
    Check(
        "fbs_completed_without_score",
        "fail",
        "Completed FBS game is missing a score",
        f"""SELECT x.season, {MATCHUP} FROM ({GAMES}) x WHERE {FBS_INVOLVED} AND completed
            AND (home_points IS NULL OR away_points IS NULL)""",
    ),
    # --- Known source gaps (model must tolerate) ----------------------------
    Check(
        "other_completed_without_score",
        "warn",
        "Completed non-FBS game is missing a score",
        f"""SELECT x.season, {MATCHUP} FROM ({GAMES}) x WHERE NOT {FBS_INVOLVED} AND completed
            AND (home_points IS NULL OR away_points IS NULL)""",
    ),
    Check(
        "fbs_game_without_stats",
        "warn",
        "Completed FBS-vs-FBS game has no advanced stats (CFBD gap)",
        f"""SELECT x.season, {MATCHUP} FROM ({GAMES}) x WHERE {FBS_VS_FBS} AND completed
            AND NOT EXISTS (SELECT 1 FROM team_game_stats s WHERE s.game_id = x.id)""",
    ),
    Check(
        "fbs_game_without_closing_line",
        "warn",
        "Completed FBS-vs-FBS game has no closing spread",
        f"""SELECT x.season, {MATCHUP} FROM ({GAMES}) x WHERE {FBS_VS_FBS} AND completed
            AND NOT EXISTS (SELECT 1 FROM market_lines m
                            WHERE m.game_id = x.id AND m.is_closing AND m.spread IS NOT NULL)""",
    ),
    Check(
        "fbs_past_game_not_final",
        "warn",
        "FBS game kicked off 2+ days ago but isn't completed (cancelled or stale)",
        f"""SELECT x.season, {MATCHUP} FROM ({GAMES}) x WHERE {FBS_INVOLVED} AND NOT completed
            AND start_time < now() - interval '2 days'""",
    ),
    Check(
        "upcoming_fbs_game_without_line",
        "warn",
        "FBS game kicking off within 3 days has no betting line yet",
        f"""SELECT x.season, {MATCHUP} FROM ({GAMES}) x WHERE {FBS_INVOLVED} AND NOT completed
            AND start_time BETWEEN now() AND now() + interval '3 days'
            AND NOT EXISTS (SELECT 1 FROM market_lines m WHERE m.game_id = x.id)""",
    ),
    Check(
        "fbs_team_few_games",
        "warn",
        "FBS team played fewer than 10 games in a finished season (2020 COVID excluded)",
        f"""SELECT g.season, t.school || ': ' || count(*) || ' games'
            FROM team_seasons ts JOIN teams t ON t.id = ts.team_id
            JOIN games g ON g.season = ts.season AND g.completed
                        AND ts.team_id IN (g.home_id, g.away_id)
            WHERE ts.division = 'fbs' AND {SEASON_FILTER}
              AND g.season <> 2020
              AND g.season < EXTRACT(year FROM now() - interval '1 month')
            GROUP BY g.season, t.school HAVING count(*) < 10""",
    ),
    Check(
        "fbs_team_missing_prior_inputs",
        "warn",
        "FBS team lacks talent or returning production (talent starts in 2015)",
        """SELECT ts.season, t.school
                  || CASE WHEN p.talent IS NULL THEN ' [no talent]' ELSE '' END
                  || CASE WHEN p.returning_ppa IS NULL THEN ' [no returning]' ELSE '' END
            FROM team_seasons ts JOIN teams t ON t.id = ts.team_id
            LEFT JOIN priors p ON p.team_id = ts.team_id AND p.season = ts.season
            WHERE ts.division = 'fbs' AND ts.season >= 2015
              AND (CAST(:season AS integer) IS NULL OR ts.season = CAST(:season AS integer))
              AND (p.talent IS NULL OR p.returning_ppa IS NULL)""",
    ),
)
