import pytest

from tsi.backtest.compare import compare_ratings


def test_identical_orderings_agree_perfectly() -> None:
    ours = {1: 20.0, 2: 5.0, 3: -3.0, 4: -15.0}
    theirs = {t: 2 * v + 1 for t, v in ours.items()}

    a = compare_ratings(ours, theirs)

    assert (a.teams, a.pearson, a.spearman) == (4, pytest.approx(1.0), pytest.approx(1.0))


def test_biggest_rank_gap_comes_first_and_only_shared_teams_count() -> None:
    ours = {1: 20.0, 2: 10.0, 3: 0.0, 4: -10.0, 5: 99.0}
    theirs = {1: 20.0, 2: 10.0, 3: -20.0, 4: 30.0}  # team 4 jumps from 4th to 1st

    a = compare_ratings(ours, theirs, top_gaps=1)

    assert a.teams == 4
    assert a.biggest_gaps[0][0] == 4
