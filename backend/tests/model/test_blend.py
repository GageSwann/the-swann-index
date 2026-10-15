import pytest

from tsi.model.blend import BlendParams, blend_rating, predictive_set, prior_weight
from tsi.model.ratings.design import POOLED_ID
from tsi.model.ratings.fit import RatingSet, TeamRating

PARAMS = BlendParams(prior_games=10, cutoff_games=8)
PRIOR, SEASON = TeamRating(20.0, 10.0), TeamRating(4.0, 2.0)


def test_prior_weight_fades_linearly_to_zero_at_cutoff() -> None:
    assert prior_weight(0, PARAMS) == 10
    assert prior_weight(4, PARAMS) == pytest.approx(5)
    assert prior_weight(8, PARAMS) == 0
    assert prior_weight(12, PARAMS) == 0


def test_no_games_means_the_prior_and_cutoff_means_the_season() -> None:
    assert blend_rating(SEASON, PRIOR, 0, PARAMS) == PRIOR
    assert blend_rating(SEASON, PRIOR, 8, PARAMS) == SEASON  # decision #23: identical after


def test_halfway_is_between() -> None:
    mid = blend_rating(SEASON, PRIOR, 4, PARAMS)  # weights 5 (prior) vs 4 (games)

    assert mid.off == pytest.approx((5 * 20 + 4 * 4) / 9)
    assert SEASON.rating < mid.rating < PRIOR.rating


def test_predictive_set_covers_teams_without_games_and_keeps_pooled_fit() -> None:
    season = RatingSet({1: SEASON, POOLED_ID: TeamRating(-20.0, -15.0)}, hfa=3.0, games={1: 2})
    priors = {1: PRIOR, 2: TeamRating(-5.0, -5.0)}

    blended = predictive_set(season, priors, prior_hfa=2.5, params=PARAMS)

    assert blended.teams[2] == priors[2]  # no games yet: pure prior
    assert blended.teams[POOLED_ID] == season.teams[POOLED_ID]
    assert 2.5 < blended.hfa < 3.0  # HFA blends too


def test_after_cutoff_predictive_equals_season() -> None:
    season = RatingSet({1: SEASON}, hfa=3.0, games={1: 9})

    blended = predictive_set(season, {1: PRIOR}, prior_hfa=2.5, params=PARAMS)

    assert blended.teams[1] == SEASON and blended.hfa == 3.0
