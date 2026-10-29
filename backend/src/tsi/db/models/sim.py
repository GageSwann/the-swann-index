"""Season simulation results, one row per FBS team per nightly rating run (doc 05 §7).

Tied to the rating run whose inputs the simulation used, so the rankings and team
pages read them alongside that run's ratings. The simulation's settings (sims, rating
uncertainty, week, seed) are in that run's `params["sim"]`.
"""

from sqlalchemy import Double, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from tsi.db.base import Base, CreatedAtMixin


class SimResult(CreatedAtMixin, Base):
    __tablename__ = "sim_results"

    run_id: Mapped[int] = mapped_column(ForeignKey("model_runs.id"), primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    expected_wins: Mapped[float]  # final wins incl. a simulated conference title game
    win_dist: Mapped[list[float]] = mapped_column(ARRAY(Double))  # P(final wins = k), k = 0..
    win_out_prob: Mapped[float]  # wins every remaining scheduled game
    title_game_prob: Mapped[float | None]  # None: no conference title game (independents)
    conference_title_prob: Mapped[float | None]
