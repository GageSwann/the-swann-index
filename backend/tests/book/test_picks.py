import pytest

from tsi.book.edges import BREAK_EVEN, GameEdges, SideEdge
from tsi.book.picks import MAX_KELLY_UNITS, PickRules, choose_picks, kelly_units, star_tier


def side(name: str, prob: float, line: float | None = 50.5, odds: int = -110, edge=None, ev=0.1):
    return SideEdge(name, line, odds, prob, prob - BREAK_EVEN if edge is None else edge, ev)


def test_star_tiers() -> None:
    thresholds = (0.015, 0.03, 0.05)

    assert [star_tier(e, thresholds) for e in (0.01, 0.015, 0.04, 0.06)] == [0, 1, 2, 3]


def test_only_edges_past_the_threshold_become_picks() -> None:
    edges = GameEdges(
        spread_diff=-2.0,
        total_diff=6.0,
        spread=side("home", 0.53, line=-3.0),  # edge 0.6 pts: no pick
        total=side("over", 0.56),  # edge 3.6 pts: 2 stars
        moneyline=None,
    )

    picks = choose_picks(edges)

    assert [(p.market, p.side, p.tier) for p in picks] == [("total", "over", 2)]
    assert picks[0].line == 50.5 and picks[0].stake_units == 1.0
    assert 0 < picks[0].kelly_units < MAX_KELLY_UNITS


def test_moneyline_needs_positive_expected_value() -> None:
    ml = side("away", 0.40, line=None, odds=150, edge=0.06, ev=-0.01)
    edges = GameEdges(None, None, None, None, ml)

    assert choose_picks(edges) == []
    assert choose_picks(GameEdges(None, None, None, None, side("away", 0.45, None, 150, 0.06)))


def test_custom_rules() -> None:
    edges = GameEdges(None, 2.0, None, side("under", 0.54), None)

    assert choose_picks(edges, PickRules(total=(0.01, 0.02, 0.03)))[0].tier == 1


def test_quarter_kelly() -> None:
    # p = 0.55 at -110: full Kelly = (0.909 * 0.55 - 0.45) / 0.909 = 5.5% -> 1.375 units
    assert kelly_units(0.55, -110) == pytest.approx(0.25 * 100 * (0.55 - 0.45 * 1.1), abs=0.01)
    assert kelly_units(0.50, -110) == 0.0
    assert kelly_units(0.80, -110) == MAX_KELLY_UNITS
