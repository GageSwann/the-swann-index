"""Save a season projection: `sim_results` rows under the rating run whose inputs it used.

The simulation's settings go into that run's `params["sim"]`, next to the rating
parameters, so a stored projection can always be traced to how it was made.
"""

from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import ModelRun, SimResult
from tsi.db.upsert import upsert_rows
from tsi.services.season_sim import SeasonProjection
from tsi.sim.season import DEFAULT_SEED


def save_season_sim(
    session_factory: sessionmaker[Session], run_id: int, projection: SeasonProjection
) -> int:
    rows = [
        {
            "run_id": run_id,
            "team_id": t.team_id,
            "expected_wins": t.expected_wins,
            "win_dist": t.win_dist,
            "win_out_prob": t.win_out_prob,
            "title_game_prob": t.title_game_prob,
            "conference_title_prob": t.conference_title_prob,
        }
        for t in projection.teams
    ]
    with session_factory.begin() as session:
        run = session.get_one(ModelRun, run_id)
        run.params = {
            **run.params,
            "sim": {
                "sims": projection.sims,
                "tau": projection.tau,
                "week": projection.week,
                "seed": DEFAULT_SEED,
            },
        }
        return upsert_rows(session, SimResult, rows)
