"""Joint score distribution for one game (doc 05 §1, v1: bivariate normal).

(margin, total) ~ bivariate normal, home view:
    margin ~ N(m, sigma_margin)
    total  ~ N(t, sigma_total(t)),  sigma_total(t) = base + slope * (t - TOTAL_PIVOT)
    corr(margin, total) = rho_per_point * m   (clipped to +-RHO_LIMIT)
Higher projected totals are noisier, and a big favorite's blowout tends to come
with a higher total; in home view that is a correlation proportional to the
home margin. Each team's score is linear in (margin, total), so team totals are
normal too:
    home = (total + margin) / 2,  away = (total - margin) / 2
Every market (doc 05 §2) is a probability from this one distribution.
"""

import math
from dataclasses import dataclass

TOTAL_PIVOT = 55.0  # points; sigma_total is quoted at this projected total
MIN_SIGMA = 5.0
RHO_LIMIT = 0.5


@dataclass(frozen=True)
class DistributionParams:
    sigma_margin: float
    sigma_total: float  # at a projected total of TOTAL_PIVOT
    sigma_total_slope: float  # extra sigma per projected point above the pivot
    rho_per_point: float  # corr(margin, total) per point of projected home margin

    def describe(self) -> str:
        return (
            f"sigma margin {self.sigma_margin:.1f} | sigma total {self.sigma_total:.1f} "
            f"{self.sigma_total_slope:+.2f}/pt above {TOTAL_PIVOT:g} | "
            f"rho {self.rho_per_point:+.4f} x home margin"
        )

    def for_game(self, margin: float, total: float) -> "ScoreDistribution":
        sigma_total = self.sigma_total + self.sigma_total_slope * (total - TOTAL_PIVOT)
        rho = max(-RHO_LIMIT, min(RHO_LIMIT, self.rho_per_point * margin))
        return ScoreDistribution(margin, total, self.sigma_margin, max(MIN_SIGMA, sigma_total), rho)


@dataclass(frozen=True)
class ScoreDistribution:
    margin: float  # mean home margin
    total: float  # mean game total
    sigma_margin: float
    sigma_total: float
    rho: float

    @property
    def home_points(self) -> float:
        return (self.total + self.margin) / 2

    @property
    def away_points(self) -> float:
        return (self.total - self.margin) / 2

    @property
    def sigma_home(self) -> float:
        return self._team_sigma(+1)

    @property
    def sigma_away(self) -> float:
        return self._team_sigma(-1)

    @property
    def home_win_prob(self) -> float:
        return self.p_margin_over(0.0)

    def p_margin_over(self, x: float) -> float:
        """P(home margin > x). Home covers a spread s (home view) when margin > -s."""
        return _p_over(self.margin, self.sigma_margin, x)

    def p_total_over(self, x: float) -> float:
        return _p_over(self.total, self.sigma_total, x)

    def p_home_over(self, x: float) -> float:
        return _p_over(self.home_points, self.sigma_home, x)

    def p_away_over(self, x: float) -> float:
        return _p_over(self.away_points, self.sigma_away, x)

    def _team_sigma(self, sign: int) -> float:
        sm, st = self.sigma_margin, self.sigma_total
        return math.sqrt(st * st + sm * sm + sign * 2 * self.rho * sm * st) / 2


def _p_over(mean: float, sigma: float, x: float) -> float:
    return 0.5 * math.erfc((x - mean) / (sigma * math.sqrt(2.0)))
