import numpy as np
import pytest

from tsi.model.key_numbers import KeyNumbers, two_way
from tsi.model.key_numbers_fit import fit_key_numbers

# Margin 3 twice as likely as its neighbours; no ties.
KEYS = KeyNumbers((0.0, 1.0, 1.0, 2.0) + (1.0,) * 57, (1.0,) * 161)


def test_tables_are_probabilities_with_no_ties_and_a_key_number_spike() -> None:
    table = KEYS.margin_table(2.5, 15.0)

    assert table.probs.sum() == pytest.approx(1.0)
    assert table.p_at(0) == 0.0
    assert table.p_at(3) == pytest.approx(2 * table.p_at(2), rel=0.1)
    assert table.p_at(-3) > table.p_at(-2)  # weights are by |margin|


def test_whole_number_lines_push_and_half_lines_do_not() -> None:
    table = KEYS.margin_table(2.5, 15.0)

    over, under, push = two_way(table, 3)
    assert push == pytest.approx(table.p_at(3)) and push > 0
    assert over + under + push == pytest.approx(1.0)
    assert two_way(table, 3.5)[2] == 0.0


def test_without_key_numbers_it_is_the_discretized_normal() -> None:
    plain = KeyNumbers.none().margin_table(0.0, 15.0)

    assert plain.p_at(0) == pytest.approx(0.0266, abs=1e-3)  # 1 / (15 sqrt(2 pi))
    assert plain.p_at(5) == pytest.approx(plain.p_at(-5))


def test_fit_recovers_a_planted_key_number() -> None:
    rng = np.random.default_rng(7)
    margins, totals = [], []
    for _ in range(4000):
        mean = float(rng.normal(0, 8))
        actual = int(np.rint(rng.normal(mean, 15)))
        if rng.random() < 0.08:  # extra games end on 3 (either way)
            actual = 3 if rng.random() < 0.5 else -3
        if actual == 0:
            actual = 1
        margins.append((mean, 15.0, actual))
        totals.append((50.0, 16.0, int(np.rint(rng.normal(50, 16)))))

    keys = fit_key_numbers(margins, totals)

    assert keys.margin[0] == 0.0
    assert keys.margin[3] > 1.8 and 0.7 < keys.margin[5] < 1.3
    assert all(0.6 < w < 1.5 for w in keys.total[30:70])  # no planted total key
