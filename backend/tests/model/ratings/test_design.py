import numpy as np
import pytest

from tsi.model.ratings.design import FCS_POOL_ID, Matchups, build_design


def dense(design, rows: int) -> np.ndarray:
    """The explicit design matrix the sparse form stands for."""
    n = design.n_teams
    x = np.zeros((rows, 2 + 2 * n))
    x[:, 0], x[:, 1] = 1.0, design.site
    x[np.arange(rows), 2 + design.off] = 1.0
    x[np.arange(rows), 2 + n + design.opp] = -1.0
    return x


def test_normal_equations_match_the_dense_design() -> None:
    rng = np.random.default_rng(3)
    teams = np.array([5, 9, 12, FCS_POOL_ID])
    team, opp = rng.choice(teams, 40), rng.choice(teams, 40)
    keep = team != opp
    matchups = Matchups(team[keep], opp[keep], rng.choice([-1.0, 0.0, 1.0], keep.sum()))
    y, w = rng.normal(size=keep.sum()), rng.uniform(0.5, 2.0, keep.sum())

    design = build_design(matchups)
    gram, rhs = design.normal_equations(y, w)

    x = dense(design, int(keep.sum()))
    assert gram == pytest.approx(x.T @ (x * w[:, None]))
    assert rhs == pytest.approx(x.T @ (w * y))


def test_team_index_is_sorted_rated_ids() -> None:
    matchups = Matchups(np.array([9, FCS_POOL_ID]), np.array([FCS_POOL_ID, 9]), np.zeros(2))

    design = build_design(matchups)

    assert design.team_index == {FCS_POOL_ID: 0, 9: 1}
    assert list(design.penalized) == [False, False, True, True, True, True]
