"""Which teams TSI rates (rule 5: never hard-coded into table design, only named here).

FBS teams are always rated individually; FCS teams from `FCS_STATS_FROM` (decision
#109). Other divisions (ii, iii, unknown), and FCS before then, are pooled by the
ratings fit. Dependency-free so every layer can import it.
"""

RATED_DIVISION = "fbs"
FCS = "fcs"

# CFBD has advanced stats for FCS-vs-FCS games from this season on (scores only before),
# so FCS teams can be rated individually from here (Phase 10, decision #107).
FCS_STATS_FROM = 2022


def rated_individually(division: str, season: int) -> bool:
    """Does a team in this division get its own rating in this season's fit?"""
    return division == RATED_DIVISION or is_individual_fcs(division, season)


def is_individual_fcs(division: str, season: int) -> bool:
    return division == FCS and season >= FCS_STATS_FROM
