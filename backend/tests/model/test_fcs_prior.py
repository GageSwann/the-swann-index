import pytest

from tsi.model.fcs_prior import FcsPrior, fit_fcs_prior
from tsi.model.ratings.design import FCS_POOL_ID
from tsi.model.ratings.types import RatingSet, TeamRating

PRIOR = FcsPrior(0.5, 0.6)


def test_regresses_last_rating_toward_the_fcs_mean() -> None:
    last = RatingSet(
        {700: TeamRating(-10.0, -8.0), 701: TeamRating(-14.0, -12.0), 5: TeamRating(9.0, 9.0)},
        3.0,
        {},
    )

    priors = PRIOR.priors([700, 701, 702], last, last_fcs=[700, 701])

    # FCS mean: off -12, def -10 (the FBS team 5 doesn't count)
    assert priors[700] == TeamRating(pytest.approx(-11.0), pytest.approx(-8.8))
    assert priors[701] == TeamRating(pytest.approx(-13.0), pytest.approx(-11.2))
    assert priors[702] == TeamRating(-12.0, -10.0)  # new FCS team: the mean


def test_pooled_last_season_gives_every_team_the_pooled_rating() -> None:
    last = RatingSet({FCS_POOL_ID: TeamRating(-11.0, -9.0)}, 3.0, {})

    assert PRIOR.priors([700], last, last_fcs=[700]) == {700: TeamRating(-11.0, -9.0)}
    assert PRIOR.priors([700], None, last_fcs=[]) == {}


def test_slope_is_the_carryover_of_ratings() -> None:
    pairs = [(TeamRating(x, 2 * x), TeamRating(0.6 * x + 1, x)) for x in (-10.0, -2.0, 4.0, 9.0)]

    fitted = fit_fcs_prior(pairs)

    assert (fitted.off_slope, fitted.def_slope) == (pytest.approx(0.6), pytest.approx(0.5))
