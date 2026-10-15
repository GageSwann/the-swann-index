"""`predictive` ratings: blend the preseason prior with this season's ratings (doc 04 §3).

    prior_weight(n) = max(0, k * (1 - n / cutoff))         n = games played
    rating          = (prior_weight * prior + n * season) / (prior_weight + n)

At n = 0 the rating is the prior; at n >= cutoff it is exactly the `season`
rating. Rankings always use `season`, so the prior only affects predictions.
Home-field advantage blends the same way, using the average games played.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from tsi.model.ratings.design import POOLED_ID
from tsi.model.ratings.fit import RatingSet, TeamRating


@dataclass(frozen=True)
class BlendParams:
    # Tuned on 2015-2022 train MAE for maximum accuracy (decision #33). Train MAE plateaus
    # for cutoffs of 14-16 games; never fading is slightly worse. Rankings never use the prior.
    prior_games: float = 6.0  # k: how many games the prior is worth before week 1
    cutoff_games: float = 14.0  # the prior is gone once a team has played this many


def prior_weight(games_played: float, params: BlendParams) -> float:
    return max(0.0, params.prior_games * (1.0 - games_played / params.cutoff_games))


def blend_rating(
    season: TeamRating, prior: TeamRating, games: float, params: BlendParams
) -> TeamRating:
    w = prior_weight(games, params)
    if w == 0:
        return season
    return TeamRating(
        off=(w * prior.off + games * season.off) / (w + games),
        defense=(w * prior.defense + games * season.defense) / (w + games),
    )


def predictive_set(
    season: RatingSet,
    priors: Mapping[int, TeamRating],
    prior_hfa: float,
    params: BlendParams | None = None,
) -> RatingSet:
    """Blend every team that has a prior or a season rating; pooled team included."""
    params = params or BlendParams()
    average = TeamRating(0.0, 0.0)
    teams = {
        team: blend_rating(
            season.teams.get(team, average),
            priors.get(team, average),
            season.games.get(team, 0),
            params,
        )
        for team in set(priors) | set(season.teams)
    }
    if POOLED_ID in season.teams:  # pooled non-FBS team: no game count; trust the season fit
        teams[POOLED_ID] = season.teams[POOLED_ID]
    played = list(season.games.values())
    avg_games = sum(played) / len(played) if played else 0.0
    w = prior_weight(avg_games, params)
    hfa = (w * prior_hfa + avg_games * season.hfa) / (w + avg_games) if w else season.hfa
    return RatingSet(teams, hfa, season.games)
