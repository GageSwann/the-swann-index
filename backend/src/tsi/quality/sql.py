"""SQL fragments shared by the quality rules."""

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
