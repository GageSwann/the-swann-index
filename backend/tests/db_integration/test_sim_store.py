"""The nightly season sim is stored under its rating run, with its settings in params."""

from datetime import UTC, datetime

from tsi.db.models import ModelRun, Team
from tsi.db.queries.sim import stored_sims
from tsi.db.queries.team_info import Record
from tsi.services.playoff_projection import TeamPlayoff
from tsi.services.season_sim import SeasonProjection, TeamProjection
from tsi.services.sim_store import save_season_sim

NOW = datetime(2026, 10, 29, 10, tzinfo=UTC)


def test_saves_one_row_per_team_and_the_settings(sessions) -> None:
    with sessions.begin() as s:
        s.add_all([Team(id=1, school="Alpha", slug="alpha"), Team(id=2, school="Bravo", slug="b")])
        s.add(
            ModelRun(
                id=7,
                kind="live",
                season=2026,
                week=9,
                season_type="regular",
                run_at=NOW,
                model_version="tsi-test",
                params={"season_hfa": 3.2},
            )
        )
    teams = [
        TeamProjection(
            1,
            "Test",
            Record(7, 0),
            5,
            11.8,
            [0.0] * 11 + [0.3, 0.7],
            0.3,
            0.99,
            0.75,
            TeamPlayoff(0.95, 0.7, [0.4, 0.3] + [0.025] * 10, 0.9, 0.6, 0.35, 0.2),
        ),
        TeamProjection(2, "FBS Independents", Record(6, 1), 5, 10.4, [0.5, 0.5], 0.5, None, None),
    ]
    projection = SeasonProjection(2026, NOW, 9, 6.1, 10_000, teams, {1: "Alpha", 2: "Bravo"})

    assert save_season_sim(sessions, 7, projection) == 2

    with sessions() as s:
        sims = stored_sims(s, 7)
        params = s.get_one(ModelRun, 7).params
    assert sims[1].expected_wins == 11.8 and sims[1].win_dist[-1] == 0.7
    assert (sims[2].title_game_prob, sims[2].conference_title_prob) == (None, None)
    assert (sims[1].playoff_prob, sims[1].champion_prob, sims[1].seed_dist[0]) == (0.95, 0.2, 0.4)
    assert sims[2].playoff_prob is None and sims[2].seed_dist is None  # no playoff odds
    assert params["season_hfa"] == 3.2  # rating params kept
    assert params["sim"] == {"sims": 10_000, "tau": 6.1, "week": 9, "seed": 2026}
