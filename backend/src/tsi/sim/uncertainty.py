"""How far a team's true strength may sit from today's estimate, for the rest of the season.

A simulated season draws one shift per team, d ~ N(0, tau), and keeps it for every
remaining game: margin = mean + d_home - d_away + e. Each game keeps the published
sigma (so single-game win probabilities match the site): only part of it moves into
the team shifts, sd(e) = sqrt(sigma^2 - 2 tau^2). The shared shift is what makes a
team's results hang together (a team that's better than expected tends to win
several of its remaining games, not one).

tau was fit on fixed-cutoff forecasts of every remaining regular-season game, 2015-2022
(the covariance of a team's residuals across its remaining games), and checked on
2023-2025 (decision #94): about 7 points preseason, shrinking as games are played.
"""

import math

TAU_PRESEASON = 7.15  # points, at week 0
TAU_PER_WEEK = -0.114  # points per week of the regular season
LAST_WEEK = 15  # the fit covers cutoffs through week 13; later weeks (and bowls) hold here


def rating_tau(regular_week: int) -> float:
    """Rating uncertainty (points) for the rest of the season, as of a regular-season week.

    Postseason weeks restart at 1 in the calendar: pass `LAST_WEEK` for them.
    """
    return TAU_PRESEASON + TAU_PER_WEEK * min(max(regular_week, 0), LAST_WEEK)


def game_noise(sigma_margin: float, tau: float) -> float:
    """Per-game noise left once both teams' shifts are drawn (keeps total sd = sigma)."""
    return math.sqrt(max(sigma_margin**2 - 2 * tau**2, 1.0))
