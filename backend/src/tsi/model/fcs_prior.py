"""Preseason priors for individually rated FCS teams (decision #109).

FCS teams have no returning production and (after 2023) no talent data, so their prior
is last season's final rating, regressed toward last season's FCS mean:
    prior = mean + slope * (last - mean)        (offense and defense separately)
The slope is how much of a team's rating carries over a season, learned on FBS teams
(final rating ~ last season's final rating). A team without last season's rating gets
the FCS mean; when last season pooled FCS (before FCS_STATS_FROM), the pooled FCS
rating stands in for the mean. Pure: no I/O.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

from tsi.model.ratings.design import FCS_POOL_ID
from tsi.model.ratings.types import AVERAGE_TEAM, RatingSet, TeamRating


@dataclass(frozen=True)
class FcsPrior:
    off_slope: float
    def_slope: float

    def priors(
        self, teams: Iterable[int], last: RatingSet | None, last_fcs: Iterable[int]
    ) -> dict[int, TeamRating]:
        """`teams`: this season's FCS teams; `last_fcs`: last season's FCS teams."""
        if last is None:
            return {}
        rated = [last.teams[t] for t in last_fcs if t in last.teams]
        if rated:
            mean = TeamRating(
                float(np.mean([r.off for r in rated])),
                float(np.mean([r.defense for r in rated])),
            )
        else:
            mean = last.teams.get(FCS_POOL_ID, AVERAGE_TEAM)
        return {t: self._regress(last.teams.get(t), mean, bool(rated)) for t in teams}

    def _regress(self, last: TeamRating | None, mean: TeamRating, individual: bool) -> TeamRating:
        if last is None or not individual:
            return mean
        return TeamRating(
            mean.off + self.off_slope * (last.off - mean.off),
            mean.defense + self.def_slope * (last.defense - mean.defense),
        )


def fit_fcs_prior(pairs: Sequence[tuple[TeamRating, TeamRating]]) -> FcsPrior:
    """`pairs`: (last season's final, this season's final) of FBS teams in train seasons."""
    if not pairs:
        return FcsPrior(0.0, 0.0)

    def slope(side: str) -> float:
        x = [getattr(last, side) for last, _ in pairs]
        y = [getattr(now, side) for _, now in pairs]
        return float(np.polyfit(x, y, 1)[0])

    return FcsPrior(slope("off"), slope("defense"))
