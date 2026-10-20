import numpy as np
import pytest

from tsi.book.consensus import ConsensusLine
from tsi.book.edges import BREAK_EVEN, EdgeShrink, cover_prob, game_edges, over_prob
from tsi.book.shrink_fit import fit_k
from tsi.model.distribution import ScoreDistribution
from tsi.model.distribution_fit import normal_cdf

# TSI: home by 7, total 58. Market: home -3, total 52.
DIST = ScoreDistribution(margin=7.0, total=58.0, sigma_margin=15.0, sigma_total=16.0, rho=0.0)
MARKET = ConsensusLine(-3.0, 52.0, -150, 130, 0.58, 3)


def test_zero_trust_means_no_edge_beyond_the_line() -> None:
    assert cover_prob(DIST, -3.0, 0.0) == pytest.approx(0.5)
    assert over_prob(DIST, 52.0, 0.0) == pytest.approx(0.5)


def test_full_trust_is_the_raw_distribution() -> None:
    assert cover_prob(DIST, -3.0, 1.0) == pytest.approx(DIST.p_margin_over(3.0))
    assert over_prob(DIST, 52.0, 1.0) == pytest.approx(DIST.p_total_over(52.0))


def test_edges_pick_the_side_tsi_likes() -> None:
    edges = game_edges(DIST, MARKET, EdgeShrink(k_spread=0.2, k_total=0.3))

    assert edges.spread_diff == pytest.approx(-7.0 - -3.0)  # TSI makes home a bigger favorite
    assert edges.total_diff == pytest.approx(6.0)
    assert edges.spread.side == "home" and edges.spread.line == -3.0
    assert edges.spread.edge == pytest.approx(edges.spread.prob - BREAK_EVEN)
    assert edges.total.side == "over"
    assert 0.5 < edges.total.prob < DIST.p_total_over(52.0)  # shrunk toward the line


def test_moneyline_edge_is_against_the_no_vig_market() -> None:
    edges = game_edges(DIST, MARKET, EdgeShrink(k_spread=1.0, k_total=0.0))
    ml = edges.moneyline

    # Full trust: TSI's win-probability shift (home by 7 vs. the market's 3) on the market's 0.58.
    shift = normal_cdf(np.array(7 / 15)) - normal_cdf(np.array(3 / 15))
    assert ml.side == "home"
    assert ml.prob == pytest.approx(0.58 + shift, abs=1e-6)
    assert ml.edge == pytest.approx(shift, abs=1e-6)
    assert ml.ev == pytest.approx(ml.prob * (100 / 150) - (1 - ml.prob))


def test_moneyline_edge_follows_tsis_disagreement_not_the_price_mapping() -> None:
    # Market moneylines make home a bigger favorite (0.76) than a normal curve maps -8.5 to
    # (~0.71). TSI likes home MORE than the market, so the moneyline lean must be home.
    dist = ScoreDistribution(13.0, 58.0, 15.4, 16.4, 0.0)
    market = ConsensusLine(-8.5, 54.5, -320, 260, 0.76, 2)

    ml = game_edges(dist, market, EdgeShrink(k_spread=0.07, k_total=0.3)).moneyline

    assert ml.side == "home" and ml.edge > 0


def test_no_market_means_no_edges() -> None:
    edges = game_edges(DIST, ConsensusLine(None, None, None, None, None, 0), EdgeShrink(0.1, 0.1))

    assert edges.spread is None and edges.total is None and edges.moneyline is None


def test_fit_k_recovers_partial_trust() -> None:
    rng = np.random.default_rng(3)
    z = rng.normal(0, 1, 40000)
    outcome = (rng.normal(0, 1, z.size) < 0.3 * z).astype(float)  # true k = 0.3

    assert fit_k(z, outcome) == pytest.approx(0.3, abs=0.03)
    assert fit_k(z, (rng.random(z.size) < 0.5).astype(float)) < 0.03  # pure noise: k ~ 0
    assert fit_k([], []) == 0.0
