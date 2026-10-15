"""`fail` rules: correctness problems (look-ahead, integrity, FBS data the model needs)."""

from tsi.quality.rule import Check
from tsi.quality.sql import FBS_INVOLVED, GAMES, MATCHUP

FAIL_RULES: tuple[Check, ...] = (
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
)
