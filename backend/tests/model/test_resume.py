import pytest

from tsi.model.resume import ScheduleGame, benchmark_rating, poisson_binomial, strength_of_record


def test_poisson_binomial_matches_binomial_for_equal_probs() -> None:
    dist = poisson_binomial([0.5, 0.5, 0.5])

    assert dist == pytest.approx([1 / 8, 3 / 8, 3 / 8, 1 / 8])
    assert sum(poisson_binomial([0.9, 0.2, 0.6, 0.35])) == pytest.approx(1.0)


def test_benchmark_is_the_twelfth_best_rating() -> None:
    assert benchmark_rating([float(x) for x in range(30)]) == 18.0
    assert benchmark_rating([5.0, 3.0]) == 3.0  # fewer than 12 teams: the last one


def schedule(opponents: list[float], won: bool = True) -> list[ScheduleGame]:
    return [ScheduleGame(o, site=0, won=won) for o in opponents]


def test_same_record_against_a_harder_schedule_is_more_impressive() -> None:
    easy = strength_of_record(schedule([-20.0] * 6), benchmark=15.0, hfa=3.0)
    hard = strength_of_record(schedule([18.0] * 6), benchmark=15.0, hfa=3.0)

    assert (easy.wins, hard.wins) == (6, 6)
    assert hard.sor < easy.sor  # less likely for a #12 team to go 6-0 vs. strong teams
    assert hard.sos > easy.sos
    assert hard.benchmark_expected_wins < easy.benchmark_expected_wins


def test_dynamic_sos_a_beaten_opponent_falling_raises_sor() -> None:
    when_they_were_good = strength_of_record(schedule([20.0]), benchmark=15.0, hfa=3.0)
    after_they_collapsed = strength_of_record(schedule([-5.0]), benchmark=15.0, hfa=3.0)

    assert when_they_were_good.sor < after_they_collapsed.sor  # the win is worth less now


def test_losses_lower_the_bar() -> None:
    games = schedule([0.0] * 3) + schedule([0.0], won=False)
    res = strength_of_record(games, benchmark=15.0, hfa=3.0)

    assert (res.wins, res.losses) == (3, 1)
    assert 0 < res.sor < 1
