"""College Football Playoff format, as data (doc 05 §7.2, decision #95).

The format has changed every year of the 12-team era, so the projector reads its rules
from here: a format change is a new `CfpFormat`, not new code.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CfpFormat:
    field_size: int
    byes: int  # top seeds skip the first round
    champion_bids: tuple[str, ...]  # these conference champions are in automatically
    group_bid_conferences: tuple[str, ...]  # the highest-ranked team among these is in
    independent_bid: tuple[str, int] | None  # (team slug, best rank needed) for its bid
    first_round: tuple[tuple[int, int], ...]  # (higher seed, lower seed), higher seed hosts
    quarterfinals: tuple[tuple[int, int], ...]  # (bye seed, first-round game index)
    semifinals: tuple[tuple[int, int], ...]  # quarterfinal indexes that meet


FORMAT_2026 = CfpFormat(
    field_size=12,
    byes=4,
    champion_bids=("ACC", "Big Ten", "Big 12", "SEC"),
    group_bid_conferences=(
        "American Athletic",
        "Conference USA",
        "Mid-American",
        "Mountain West",
        "Pac-12",
        "Sun Belt",
    ),
    independent_bid=("notre-dame", 12),
    first_round=((5, 12), (6, 11), (7, 10), (8, 9)),
    # No re-seeding: 1 meets the 8/9 winner, 2 the 7/10, 3 the 6/11, 4 the 5/12.
    quarterfinals=((1, 3), (2, 2), (3, 1), (4, 0)),
    # The 1 and 4 quarterfinals meet, and the 2 and 3 (doc 05 §7.2).
    semifinals=((0, 3), (1, 2)),
)
