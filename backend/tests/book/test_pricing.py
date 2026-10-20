import pytest

from tsi.book.config import BookConfig
from tsi.book.odds import prob_from_american
from tsi.book.pricing import price_game, round_half
from tsi.model.distribution import ScoreDistribution

# Home favored by 6.8, total 54.3.
DIST = ScoreDistribution(margin=6.8, total=54.3, sigma_margin=15.2, sigma_total=16.4, rho=0.05)


def test_main_lines_round_the_fair_line_to_half_points() -> None:
    m = price_game(DIST)

    assert m.fair_spread == pytest.approx(-6.8) and m.spread.line == -7.0
    assert m.fair_total == pytest.approx(54.3) and m.total.line == 54.5
    assert m.home_total.line == 30.5 and m.away_total.line == 24.0
    assert (m.spread.first.book, m.spread.second.book) == (-110, -110)


def test_spread_probabilities_are_home_view() -> None:
    m = price_game(DIST)

    # Home -7 when TSI has home by 6.8: home covers slightly less than half the time.
    assert m.spread.first.prob < 0.5 < m.spread.second.prob
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

    assert [t.line for t in m.alt_spreads] == [-10.0, -9.0, -8.0, -7.0, -6.0, -5.0, -4.0]
    covers = [t.first.prob for t in m.alt_spreads]
    assert covers == sorted(covers)  # bigger home handicap -> harder to cover
    overs = [t.first.prob for t in m.alt_totals]
    assert overs == sorted(overs, reverse=True)


def test_unflat_main_lines_are_priced_from_probability() -> None:
    m = price_game(DIST, BookConfig(main_line_odds=None))

    assert m.spread.second.book < -110  # TSI likes the away side at +7, so it costs more


def test_round_half() -> None:
    assert [round_half(x) for x in (-6.8, -3.25, 3.25, 54.74, 0.2)] == [-7.0, -3.0, 3.5, 54.5, 0.0]
