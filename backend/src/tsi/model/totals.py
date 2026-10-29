"""Predictive total (doc 04 §6): a learned blend of pre-kickoff scoring and pace signals.

    total = sum_k beta[b, k] * feature_k        b = season-stage bucket (as the margin stack)

Features (game totals, both teams combined):
    level       league scoring level: this season's average FBS game total so far,
                shrunk toward last season's (`LEVEL_SHRINK` team-games of weight)
    ppd         opponent-adjusted points-per-drive sum (points above average)
    success     opponent-adjusted success-rate sum (successful plays above average)
    pace        expected drives above average (this season)
    tempo       expected plays above average (this season)
    prior       preseason prior offense-vs-defense sum (points)
    last_pace   last season's final pace sum (drives)
    last_tempo  last season's final tempo sum (plays)
Fit with the margin stack's machinery (`fit_stack`); `level` is unpenalized so the
other weights only explain deviations from the scoring environment. Selection on
2015-22 walk-forward games (decision #50): adding last season's PPD did not help.
"""

TOTAL_FEATURES = (
    "level",
    "ppd",
    "success",
    "pace",
    "tempo",
    "prior",
    "last_pace",
    "last_tempo",
)
TOTAL_UNPENALIZED = ("level",)
LEVEL_SHRINK = 300  # team-games (~2 weeks of FBS games); insensitive between 100 and 1500


def scoring_level(now: float | None, last: float, team_games: int) -> float:
    """Blend this season's league game total with last season's as games accrue."""
    if now is None:
        return last
    return (team_games * now + LEVEL_SHRINK * last) / (team_games + LEVEL_SHRINK)
