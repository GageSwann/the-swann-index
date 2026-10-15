import numpy as np
import pytest

from tsi.model.stack import FEATURES, StackSample, fit_stack, stage_bucket


@pytest.mark.parametrize(
    ("games", "bucket"), [(0, 0), (1, 1), (3, 3), (4, 4), (5, 4), (6, 5), (8, 5), (9, 6), (14, 6)]
)
def test_stage_buckets(games: int, bucket: int) -> None:
    assert stage_bucket(games) == bucket


def samples(bucket: int, beta: list[float], n: int = 400) -> list[StackSample]:
    rng = np.random.default_rng(bucket)
    out = []
    for _ in range(n):
        x = (float(rng.integers(0, 2)), *rng.normal(0, 10, size=len(FEATURES) - 1))
        out.append(StackSample(bucket, tuple(x), float(np.dot(beta, x))))
    return out


def test_learns_separate_weights_per_stage() -> None:
    early = [3.0, 0.1, 0.1, 1.0, 0.5]  # leans on the prior
    late = [3.0, 0.7, 0.6, 0.1, 0.3]  # leans on this season's stats
    model = fit_stack(samples(0, early) + samples(6, late), lam=0.0)

    assert model.coefs[0] == pytest.approx(early, abs=1e-6)
    assert model.coefs[6] == pytest.approx(late, abs=1e-6)


def test_ridge_shrinks_signals_but_not_home_field() -> None:
    beta = [3.0, 0.7, 0.6, 0.1, 0.3]
    loose = fit_stack(samples(4, beta, n=50), lam=0.0).coefs[4]
    tight = fit_stack(samples(4, beta, n=50), lam=1e5).coefs[4]

    assert abs(tight[1]) < abs(loose[1])  # ppd weight shrunk
    assert tight[0] > 1.0  # site stays meaningful


def test_unseen_stage_borrows_the_nearest() -> None:
    model = fit_stack(samples(5, [3.0, 0.7, 0.6, 0.1, 0.3]), lam=0.0)
    x = (1.0, 2.0, 3.0, 4.0, 5.0)

    assert model.predict(6, x) == pytest.approx(model.predict(5, x))
