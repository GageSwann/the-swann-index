import pytest

from tsi.model.features import GameSide, margin_features, total_features
from tsi.model.ratings.components import Components, MetricRatings
from tsi.model.ratings.types import TeamRating
from tsi.model.totals import TOTAL_FEATURES


def metric(teams: dict[int, TeamRating], level: float) -> MetricRatings:
    return MetricRatings(teams, hfa=0.0, level=level)


def components(level: float, home_off: float) -> Components:
    teams = {1: TeamRating(home_off, 0.0), 2: TeamRating(0.0, 2.0)}
    return Components(
        ppd=metric(teams, level / 2),
        success=metric(teams, 0.0),
        pace=metric({1: TeamRating(1.0, 0.0)}, 12.0),
        tempo=None,
        games={1: 3, 2: 3},
    )


def test_total_features_add_both_offenses_against_both_defenses() -> None:
    side = GameSide(home=1, away=2, neutral=False)

    feats = dict(
        zip(TOTAL_FEATURES, total_features(side, components(56.0, 5.0), None, {}), strict=True)
    )

    assert feats["ppd"] == pytest.approx(5.0 - 2.0)  # (home off - away def) + (away off - 0)
    assert feats["pace"] == pytest.approx(1.0)
    assert feats["tempo"] == 0.0  # no plays fit yet
    assert feats["last_pace"] == 0.0  # no last season
    assert 0 < feats["level"] < 56.0  # 6 team-games: mostly last season's (missing = 0)


def test_margin_features_are_home_view() -> None:
    side = GameSide(home=1, away=2, neutral=True)
    priors = {1: TeamRating(3.0, 1.0), 2: TeamRating(0.0, 0.0)}

    site, ppd, _, prior, elo = margin_features(side, components(56.0, 5.0), priors, 2.5)

    assert site == 0.0 and elo == 2.5
    assert ppd == pytest.approx((5.0 - 2.0) - (0.0 - 0.0))
    assert prior == pytest.approx(4.0)
