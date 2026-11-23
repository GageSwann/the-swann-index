"""The official FCS playoff brackets, entered by hand once the field is announced (#157).

CFBD lists the first-round games but not the seeds or which first-round winner meets
which bye seed, so the bracket comes from the NCAA's announcement (selection Sunday).
`field` lists the 24 teams by position in `sim/fcs_format.py`'s bracket: seeds 1-16, then
the unseeded teams at positions 17-24, where position p meets seed 33 - p in the first
round (17 plays at 16, ..., 24 at 9) and that winner meets bye seed p - 16 (17's game
feeds seed 1, ..., 24's feeds seed 8). The nightly run checks the first round against
CFBD's games and ignores a bracket that doesn't match.
"""

from dataclasses import dataclass

from tsi.sim.fcs_format import FcsFormat


@dataclass(frozen=True)
class OfficialBracket:
    season: int
    field: tuple[str, ...]  # team slugs by position (1 = the top seed)

    def first_round(self, fmt: FcsFormat) -> list[tuple[str, str]]:
        """(seeded host, unseeded visitor) slugs of every first-round game."""
        return [(self.field[hi - 1], self.field[lo - 1]) for hi, lo in fmt.first_round]


FCS_BRACKETS = {
    # Announced Sunday, Nov 22, 2026 (NCAA). Quarterfinals by seed: 1/8 v 4/5, 2/7 v 3/6.
    2026: OfficialBracket(
        2026,
        (
            "montana-state",  # 1
            "tarleton-state",
            "south-dakota-state",
            "lamar",
            "stephen-f-austin",
            "youngstown-state",
            "south-dakota",
            "mercer",  # 8
            "north-dakota",  # 9
            "northern-arizona",
            "tennessee-tech",
            "lehigh",
            "illinois-state",
            "weber-state",
            "montana",
            "monmouth",  # 16
            "harvard",  # 17: at 16 Monmouth; the winner meets 1 Montana State
            "incarnate-word",  # 18: at 15 Montana -> 2 Tarleton State
            "western-illinois",  # 19: at 14 Weber State -> 3 South Dakota State
            "austin-peay",  # 20: at 13 Illinois State -> 4 Lamar
            "ualbany",  # 21: at 12 Lehigh -> 5 Stephen F. Austin
            "dayton",  # 22: at 11 Tennessee Tech -> 6 Youngstown State
            "long-island-university",  # 23: at 10 Northern Arizona -> 7 South Dakota
            "idaho-state",  # 24: at 9 North Dakota -> 8 Mercer
        ),
    ),
}
