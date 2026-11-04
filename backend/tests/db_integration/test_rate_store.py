"""Nightly ratings: FBS teams ranked, individually rated FCS teams stored unranked (#109)."""

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
        [TeamRanking(1, 12.0, 8.0, 4.0, 9, False, 1, Resume(8, 1, 0.3, 7.5, 2.0), 1)],
        {},
        {700: ratings.teams[700], 701: ratings.teams[701]},
    )
    return LiveRatings(2026, NOW, rankings, [PredictiveTeam(1, Rating(9.0, 4.0), 9, False)], 2.9)


@pytest.mark.db
def test_fcs_teams_are_stored_unranked_with_the_fcs_average_as_fallback(sessions) -> None:
    with sessions.begin() as s:
        s.add_all([Team(id=t, school=f"T{t}", slug=f"t{t}") for t in (1, 700, 701)])
        s.add(
            CalendarWeek(season=2026, season_type="regular", week=10, start_date=NOW, end_date=NOW)
        )

    run_id = save_live_ratings(sessions, live(), load_artifact())

    with sessions() as s:
        rows = {(r.team_id, r.basis): r for r in s.scalars(select(TeamRating))}
        params = s.get(ModelRun, run_id).params
    assert set(rows) == {(1, "season"), (1, "predictive"), (700, "season"), (701, "season")}
    fcs = rows[(701, "season")]
    assert (fcs.rating, fcs.rank_power, fcs.rank_resume, fcs.sor) == (-40.0, None, None, None)
    assert (fcs.games_played, fcs.provisional) == (3, True)
    assert rows[(1, "season")].rank_power == 1
    pooled = params["pooled_season_ratings"]
    assert pooled == {"fcs": pytest.approx(-35.0), "lower": -50.0}  # FCS average; lower pool
