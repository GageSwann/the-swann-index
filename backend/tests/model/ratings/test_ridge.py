import numpy as np
import pytest

from tsi.model.ratings.ridge import weighted_ridge


def test_zero_penalty_recovers_exact_coefficients() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(size=(50, 3))
    beta = np.array([1.0, -2.0, 0.5])

    coef = weighted_ridge(x, x @ beta, np.ones(50), lam=0.0, penalized=np.ones(3, dtype=bool))

    assert coef == pytest.approx(beta, abs=1e-6)


def test_penalty_shrinks_only_penalized_columns() -> None:
    x = np.array([[1.0, 1.0], [1.0, -1.0], [1.0, 1.0], [1.0, -1.0]])
    y = np.array([5.0, 1.0, 5.0, 1.0])  # intercept 3, slope 2
    penalized = np.array([False, True])

    coef = weighted_ridge(x, y, np.ones(4), lam=4.0, penalized=penalized)

    assert coef[0] == pytest.approx(3.0)  # unpenalized: untouched
    assert 0 < coef[1] < 2.0  # shrunk toward 0


def test_uninformative_unpenalized_column_is_zero_not_an_error() -> None:
    x = np.array([[1.0, 0.0], [1.0, 0.0]])  # second column all zeros (e.g. HFA, all neutral)

    coef = weighted_ridge(
        x, np.array([2.0, 4.0]), np.ones(2), lam=1.0, penalized=np.zeros(2, dtype=bool)
    )

    assert coef == pytest.approx([3.0, 0.0])
