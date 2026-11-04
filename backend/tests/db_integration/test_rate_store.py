"""Nightly ratings: FBS and FCS teams ranked within their own division (#109, #111)."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from tsi.db.models import CalendarWeek, ModelRun, Team, TeamRating
from tsi.model.artifact import load_artifact
from tsi.model.ratings.design import LOWER_POOL_ID
from tsi.model.ratings.types import RatingSet
from tsi.model.ratings.types import TeamRating as Rating
from tsi.model.resume import Resume
from tsi.services.compute_rankings import Rankings, TeamRanking
from tsi.services.rate import LiveRatings, PredictiveTeam
from tsi.services.rate_store import save_live_ratings

NOW = datetime(2026, 11, 4, 10, tzinfo=UTC)


def ranked(team: int, rating: float, games: int, power: int, resume: int) -> TeamRanking:
    return TeamRanking(team, rating, rating, 0.0, games, games < 4, power,
                       Resume(5, 2, 0.4, 5.1, -1.0), resume)  # fmt: skip


def live() -> LiveRatings:
    ratings = RatingSet(
        {1: Rating(8.0, 4.0), 700: Rating(-20.0, -10.0), 701: Rating(-25.0, -15.0),
         LOWER_POOL_ID: Rating(-30.0, -20.0)},
        3.0,
        {1: 9, 700: 8, 701: 3},
    )  # fmt: skip
    rankings = Rankings(
        2026,
        NOW,
        ratings,
        6.0,
        [ranked(1, 12.0, 9, 1, 1)],
        {},
        fcs_benchmark=-33.0,
        fcs_teams=[ranked(700, -30.0, 8, 1, 2), ranked(701, -40.0, 3, 2, 1)],
    )
    predictive = [
        PredictiveTeam(1, Rating(9.0, 4.0), 9, False),
        PredictiveTeam(700, Rating(-18.0, -9.0), 8, False, "fcs"),
        PredictiveTeam(701, Rating(-17.0, -9.0), 3, True, "fcs"),
    ]
    return LiveRatings(2026, NOW, rankings, predictive, 2.9)


@pytest.mark.db
def test_each_division_is_ranked_on_its_own(sessions) -> None:
    with sessions.begin() as s:
        s.add_all([Team(id=t, school=f"T{t}", slug=f"t{t}") for t in (1, 700, 701)])
        s.add(
            CalendarWeek(season=2026, season_type="regular", week=10, start_date=NOW, end_date=NOW)
        )

    run_id = save_live_ratings(sessions, live(), load_artifact())

    with sessions() as s:
        rows = {(r.team_id, r.basis): r for r in s.scalars(select(TeamRating))}
        params = s.get(ModelRun, run_id).params
    assert len(rows) == 6  # season + predictive for every team
    fcs = rows[(701, "season")]
    assert (fcs.rating, fcs.rank_power, fcs.rank_resume, fcs.sor) == (-40.0, 2, 1, 0.4)
    assert (fcs.games_played, fcs.provisional) == (3, True)
    assert rows[(1, "season")].rank_power == 1
    # Predictive ranks within each division: 701 (-26) edges 700 (-27) among FCS teams.
    assert [rows[(t, "predictive")].rank_power for t in (1, 700, 701)] == [1, 2, 1]
    assert params["fcs_resume_benchmark"] == -33.0
    assert params["pooled_season_ratings"] == {"fcs": pytest.approx(-35.0), "lower": -50.0}
