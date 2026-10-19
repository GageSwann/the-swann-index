"""Season ratings (rankings): learned blend of this-season components (decision #38).

    off  = w_ppd * off_ppd + w_success * off_success        (same for def)
    HFA  = a constant learned with the weights

The weights were learned on 2015-2022 walk-forward games (one weight set for the
whole season) and use ONLY this season's games: no prior, no Elo, no history.
Ratings are points per game vs. an average FBS team; def > 0 means a good defense.
EPA is not fitted: it did not improve either rating set (decision #38).
"""

from collections.abc import Sequence
from dataclasses import dataclass

from tsi.model.ratings.components import Components, StatRow, fit_components
from tsi.model.ratings.types import AVERAGE_TEAM, RatingSet, TeamRating, matchup_margin

__all__ = ["AVERAGE", "RatingParams", "RatingSet", "StatRow", "TeamRating", "fit_ratings"]


@dataclass(frozen=True)
class RatingParams:
    lam: float = 2.0  # ridge penalty on standardized targets (shrinkage toward average)
    # Learned on 2015-2022 (least squares on walk-forward margins; LOSO train MAE 14.04,
    # validation 13.36 vs. 13.51 for the old hand-set 75/25 PPD/EPA blend).
    ppd_weight: float = 0.726
    success_weight: float = 0.635
    hfa: float = 3.24  # points of margin for the home team


AVERAGE = RatingSet(teams={}, hfa=0.0, games={})


def fit_ratings(rows: Sequence[StatRow], params: RatingParams | None = None) -> RatingSet:
    """Ratings from completed team-game rows (this season only, before the cutoff)."""
    params = params or RatingParams()
    components = fit_components(rows, params.lam)
    return AVERAGE if components is None else blend_components(components, params)


def blend_components(components: Components, params: RatingParams) -> RatingSet:
    ppd, success = components.ppd, components.success
    if success is None:  # no advanced stats yet: PPD carries both weights
        w_ppd, w_sr, success = params.ppd_weight + params.success_weight, 0.0, ppd
    else:
        w_ppd, w_sr = params.ppd_weight, params.success_weight

    def mix(team: int) -> TeamRating:
        a, b = ppd.teams.get(team, AVERAGE_TEAM), success.teams.get(team, AVERAGE_TEAM)
        return TeamRating(w_ppd * a.off + w_sr * b.off, w_ppd * a.defense + w_sr * b.defense)

    return RatingSet({team: mix(team) for team in ppd.teams}, params.hfa, components.games)


def predicted_margin(
    ratings: RatingSet, home: TeamRating, away: TeamRating, neutral: bool
) -> float:
    """Home-view margin: (home off - away def) - (away off - home def) + HFA."""
    return matchup_margin(home, away) + (0.0 if neutral else ratings.hfa)
