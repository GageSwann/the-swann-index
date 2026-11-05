"""A playoff bracket's rounds as data the site can draw without knowing the format.

Each game has two slots: a position in the projected field (1 = the top seed) or the
winner of a game in the previous round. `advance` names the playoff-odds field that
decides who moves on in the projected bracket (the team likelier to reach the next
round). The FCS first round uses the quarterfinal odds: reaching the second round
isn't stored, and the likelier quarterfinalist is the stronger team.
"""

from dataclasses import dataclass

from tsi.sim.cfp_format import CfpFormat
from tsi.sim.fcs_format import FcsFormat


@dataclass(frozen=True)
class BracketSlot:
    seed: int | None = None  # position in the projected field (1-based)
    game: int | None = None  # or: the winner of this game in the previous round


@dataclass(frozen=True)
class BracketRound:
    name: str
    note: str | None
    advance: str  # PlayoffTeam field: the chance of reaching the next round
    games: list[list[BracketSlot]]


def _seeds(pairs) -> list[list[BracketSlot]]:
    return [[BracketSlot(seed=a), BracketSlot(seed=b)] for a, b in pairs]


def _winners(pairs) -> list[list[BracketSlot]]:
    return [[BracketSlot(game=a), BracketSlot(game=b)] for a, b in pairs]


FINAL = [[BracketSlot(game=0), BracketSlot(game=1)]]


def cfp_rounds(fmt: CfpFormat) -> list[BracketRound]:
    return [
        BracketRound(
            "First round", "At the higher seed", "quarterfinal_prob", _seeds(fmt.first_round)
        ),
        BracketRound(
            "Quarterfinals",
            None,
            "semifinal_prob",
            [[BracketSlot(seed=s), BracketSlot(game=g)] for s, g in fmt.quarterfinals],
        ),
        BracketRound("Semifinals", None, "final_prob", _winners(fmt.semifinals)),
        BracketRound("Championship", None, "champion_prob", FINAL),
    ]


def fcs_rounds(fmt: FcsFormat) -> list[BracketRound]:
    return [
        BracketRound(
            "First round", "At the better-placed team", "quarterfinal_prob", _seeds(fmt.first_round)
        ),
        BracketRound(
            "Second round",
            "At the seeded team",
            "quarterfinal_prob",
            [[BracketSlot(seed=s), BracketSlot(game=g)] for s, g in fmt.second_round],
        ),
        BracketRound(
            "Quarterfinals", "At the higher seed", "semifinal_prob", _winners(fmt.quarterfinals)
        ),
        BracketRound("Semifinals", "At the higher seed", "final_prob", _winners(fmt.semifinals)),
        BracketRound("Championship", "Neutral site", "champion_prob", FINAL),
    ]
