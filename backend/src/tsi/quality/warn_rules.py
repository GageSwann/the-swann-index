"""`warn` rules: known CFBD source gaps the model must tolerate."""

from tsi.quality.rule import Check
from tsi.quality.sql import FBS_INVOLVED, FBS_VS_FBS, GAMES, MATCHUP, SEASON_FILTER

WARN_RULES: tuple[Check, ...] = (
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
