"""A team's projected season from the stored simulation (decision #98)."""

from dataclasses import dataclass

from tsi.db.queries.sim import StoredSim


@dataclass(frozen=True)
class Projection:
    expected_wins: float  # final wins incl. a simulated conference title game
    win_dist: list[float]  # P(final wins = k) for k = 0, 1, ...
    win_out_prob: float  # wins every remaining scheduled game
    title_game_prob: float | None  # None: no conference title game (independents)
    conference_title_prob: float | None
    playoff_prob: float | None  # None outside the regular season
    champion_prob: float | None  # national title


def projection(sim: StoredSim | None) -> Projection | None:
    if sim is None:
        return None
    return Projection(
        expected_wins=sim.expected_wins,
        win_dist=sim.win_dist,
        win_out_prob=sim.win_out_prob,
        title_game_prob=sim.title_game_prob,
        conference_title_prob=sim.conference_title_prob,
        playoff_prob=sim.playoff_prob,
        champion_prob=sim.champion_prob,
    )
