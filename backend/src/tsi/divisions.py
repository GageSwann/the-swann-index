"""The division TSI rates (rule 5: never hard-coded into table design, only named here).

Other divisions (fcs, ii, iii, unknown) are stored per season in `team_seasons` and
pooled by the ratings fit. Dependency-free so every layer can import it.
"""

RATED_DIVISION = "fbs"

# CFBD has advanced stats for FCS-vs-FCS games from this season on (scores only before),
# so FCS teams can be rated individually from here (Phase 10, decision #107).
FCS_STATS_FROM = 2022
