import pytest

from tsi.model.ratings.types import RatingSet, TeamRating
from tsi.model.resume import FCS_BENCHMARK_RANK, ScheduleGame
from tsi.services.compute_rankings import rank_division

# Twelve FCS teams rated -10, -12, ..., -32; team 700 is the best.
RATINGS = RatingSet({700 + i: TeamRating(-10.0 - 2 * i, 0.0) for i in range(12)}, 3.0,
                    {700 + i: 6 for i in range(12)})  # fmt: skip


def test_ranks_within_the_division_against_its_own_benchmark() -> None:
    schedules = {t: [ScheduleGame(-20.0, 1, True)] for t in RATINGS.teams}
    schedules[711] = [ScheduleGame(-20.0, 1, True)] * 3  # three wins: the best résumé

    teams, benchmark = rank_division(
        set(RATINGS.teams) | {999}, RATINGS, schedules, FCS_BENCHMARK_RANK, 15.0
    )

    assert benchmark == pytest.approx(-28.0)  # the #10 team's rating
    assert [t.team_id for t in teams[:2]] == [700, 701]  # Power: by rating; 999 is unrated
    assert len(teams) == 12 and teams[0].rank_power == 1
    best_resume = min(teams, key=lambda t: t.rank_resume)
    assert best_resume.team_id == 711 and best_resume.resume.wins == 3
