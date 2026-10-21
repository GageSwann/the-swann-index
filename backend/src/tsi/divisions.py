"""The division TSI rates (rule 5: never hard-coded into table design, only named here).

Other divisions (fcs, ii, iii, unknown) are stored per season in `team_seasons` and
pooled by the ratings fit. Dependency-free so every layer can import it.
"""

RATED_DIVISION = "fbs"
