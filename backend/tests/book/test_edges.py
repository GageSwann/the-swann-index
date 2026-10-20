import numpy as np
import pytest

from tsi.book.consensus import ConsensusLine
from tsi.book.edges import BREAK_EVEN, EdgeShrink, cover_prob, game_edges, over_prob
from tsi.book.shrink_fit import fit_k
from tsi.model.distribution import ScoreDistribution

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

    assert ml.side == "home"
    assert ml.prob == pytest.approx(DIST.home_win_prob)
    assert ml.edge == pytest.approx(DIST.home_win_prob - 0.58)
    assert ml.ev == pytest.approx(ml.prob * (100 / 150) - (1 - ml.prob))


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
