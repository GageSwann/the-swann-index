import numpy as np
import pytest

from tsi.model.ratings.types import TeamRating, matchup_margin
from tsi.model.stack import StackModel
from tsi.model.stack_team import TeamSignals, predictive_hfa, predictive_rating

# site, ppd, success, prior, elo, second, power
MODEL = StackModel({4: np.array([2.5, 0.3, 0.6, 0.4, 0.25, 0.1, 0.2])})
ELO_PER_POINT, ELO_HFA = 22.0, 55.0


def signals(ppd, sr, prior, elo, second=(0.0, 0.0), power=(0.0, 0.0)):
    return TeamSignals(
        TeamRating(*ppd),
        TeamRating(*sr),
        TeamRating(*prior),
        elo / ELO_PER_POINT,
        TeamRating(*second),
        TeamRating(*power),
    )


def test_team_ratings_reproduce_the_stack_margin_exactly() -> None:
    home_elo, away_elo = 1620.0, 1480.0
    home = signals((6.0, 2.0), (4.0, 1.0), (10.0, 3.0), home_elo, (3.0, -1.0), (0.5, 0.2))
    away = signals((-1.0, 3.0), (0.5, -2.0), (-2.0, 1.0), away_elo, (-2.0, 1.5), (0.1, -0.4))

    features = (
        1.0,  # home game
        matchup_margin(home.ppd, away.ppd),
        matchup_margin(home.success, away.success),
        (home.prior.off + home.prior.defense) - (away.prior.off + away.prior.defense),
        (home_elo - away_elo + ELO_HFA) / ELO_PER_POINT,
        matchup_margin(home.second, away.second),
        matchup_margin(home.power, away.power),
    )
    stack_margin = MODEL.predict(4, features)

    h, a = predictive_rating(MODEL, 4, home), predictive_rating(MODEL, 4, away)
    team_margin = h.rating - a.rating + predictive_hfa(MODEL, 4, ELO_HFA / ELO_PER_POINT)

    assert team_margin == pytest.approx(stack_margin)
