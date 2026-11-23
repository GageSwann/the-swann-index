import pytest

from tsi.book.config import BookConfig
from tsi.book.odds import prob_from_american
from tsi.book.pricing import _markets, half_point, price_game
from tsi.model.distribution import DistributionParams, ScoreDistribution

# Home favored by 6.8, total 54.3.
DIST = ScoreDistribution(margin=6.8, total=54.3, sigma_margin=15.2, sigma_total=16.4, rho=0.05)


def test_main_lines_round_the_fair_line_to_half_points() -> None:
    m = price_game(DIST)

    # Always on a .5 (#187): home by 6.8 -> -6.5, total 54.3 -> 54.5, team totals too.
    assert m.fair_spread == pytest.approx(-6.8) and m.spread.line == -6.5
    assert m.fair_total == pytest.approx(54.3) and m.total.line == 54.5
    assert m.home_total.line == 30.5 and m.away_total.line == 23.5
    assert m.spread.push == m.total.push == 0.0  # a half point never pushes
    assert (m.spread.first.book, m.spread.second.book) == (-110, -110)


def test_spread_probabilities_are_home_view() -> None:
    m = price_game(DIST)

    # Home -6.5 when TSI has home by 6.8: home covers slightly more than half the time.
    assert m.spread.second.prob < 0.5 < m.spread.first.prob
    assert m.spread.first.prob + m.spread.second.prob == pytest.approx(1.0)


def test_moneyline_has_the_configured_hold() -> None:
    m = price_game(DIST)
    ml = m.moneyline

    assert ml.first.prob == pytest.approx(DIST.home_win_prob)
    assert ml.first.fair < 0 < ml.second.fair  # home is the favorite
    implied = prob_from_american(ml.first.book) + prob_from_american(ml.second.book)
    assert 1 - 1 / implied == pytest.approx(0.045, abs=0.003)  # odds are whole numbers


def test_alt_ladder_is_monotone_around_the_main_line() -> None:
    m = price_game(DIST, BookConfig(ladder_width=3, ladder_step=1))

    assert [t.line for t in m.alt_spreads] == [-9.5, -8.5, -7.5, -6.5, -5.5, -4.5, -3.5]
    covers = [t.first.prob for t in m.alt_spreads]
    assert covers == sorted(covers)  # bigger home handicap -> harder to cover
    overs = [t.first.prob for t in m.alt_totals]
    assert overs == sorted(overs, reverse=True)


def test_unflat_main_lines_are_priced_from_probability() -> None:
    m = price_game(DIST, BookConfig(main_line_odds=None))

    assert m.spread.first.book < -110  # TSI likes the home side at -6.5, so it costs more


def test_half_point() -> None:
    xs = (-8.8, -8.6, 9.0, -9.0, 45.2, 44.9, 0.2, 0.0)
    assert [half_point(x) for x in xs] == [-8.5, -8.5, 9.5, -9.5, 45.5, 44.5, 0.5, 0.5]
    assert all(half_point(-x) == -half_point(x) for x in (0.3, 3.0, 7.7, 13.5))  # mirror


def test_key_numbers_add_a_push_and_price_the_decided_outcomes() -> None:
    from tsi.model.key_numbers import KeyNumbers

    keys = KeyNumbers((0.0, 1.0, 1.0, 2.5) + (1.0,) * 57, (1.0,) * 161)
    dist = DistributionParams(15.4, 16.4, 0.12, 0.0075).for_game(3.0, 50.0)  # home by 3

    markets = price_game(dist, keys=keys)
    cover, _ = _markets(dist, keys)

    # A whole-number line (the market's, in the Book's edges) can push on a key number;
    # TSI's own main line is a half point (#187), so it never does.
    whole_prob, whole_push = cover(-3.0)
    assert whole_push > 0.05 and cover(-3.5)[1] == 0.0
    assert 0.0 < whole_prob < 1.0  # P(home covers | no push)
    assert markets.spread.line == -3.5 and markets.spread.push == 0.0  # exactly 3 -> 3.5
    assert markets.moneyline.push == 0.0
    assert markets.moneyline.first.prob == pytest.approx(dist.home_win_prob)  # unchanged
