"""FCS playoff format, as data (Phase 11, decision #125), like sim/cfp_format.py.

2026-27 (NCAA, owner): 24 teams, automatic bids for the champions of the 11 conferences
below, at-large bids by the committee stand-in (FCS Résumé). The top 16 are seeded: seeds
1-8 get a first-round bye, seeds 9-16 host the 8 unseeded teams in the first round. Games
are on campus (the better seed hosts) until the final in Nashville (neutral). Unseeded
teams are placed by rank here (the real placement is regional). The SWAC and MEAC skip
the playoff (the Celebration Bowl); the Ivy League has played in it since 2025.

Ineligible teams (doc 05 §7.5): teams moving up from Division II/III, during their first
`reclass_seasons` FCS seasons (found from `team_seasons`), and teams in their final FCS
season before FBS (`moving_up`, by slug: data can't know a future move).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FcsFormat:
    field_size: int
    seeds: int  # seeded teams
    byes: int  # the top seeds skip the first round
    champion_bids: tuple[str, ...]  # these conference champions are in automatically
    no_playoff: tuple[str, ...]  # conferences that don't take part
    title_game_conferences: tuple[str, ...]  # FCS conferences that play a title game
    moving_up: tuple[str, ...]  # slugs: last FCS season before FBS (ineligible)
    reclass_seasons: int  # seasons a team moving up from D-II/III is ineligible
    first_round: tuple[tuple[int, int], ...]  # (seed, position), the seed hosts
    second_round: tuple[tuple[int, int], ...]  # (bye seed, first-round game index), seed hosts
    quarterfinals: tuple[tuple[int, int], ...]  # second-round game indexes that meet
    semifinals: tuple[tuple[int, int], ...]  # quarterfinal indexes that meet


FCS_FORMAT_2026 = FcsFormat(
    field_size=24,
    seeds=16,
    byes=8,
    champion_bids=(
        "Big Sky",
        "Coastal Athletic",
        "Ivy",
        "MVFC",
        "NEC",
        "OVC",
        "Patriot",
        "Pioneer",
        "Southern",  # SoCon
        "Southland",
        "UAC",
    ),
    no_playoff=("MEAC", "SWAC"),
    title_game_conferences=("SWAC",),
    moving_up=(),
    reclass_seasons=4,
    # Seeds 9-16 host positions 17-24 (the unseeded teams by rank): 9 v 24, ..., 16 v 17.
    first_round=tuple((9 + i, 24 - i) for i in range(8)),
    # Seed s meets the winner of game 8 - s: 1 gets the 16/17 winner, 8 the 9/24 winner.
    second_round=tuple((s, 8 - s) for s in range(1, 9)),
    # By seed: 1/8 v 4/5 and 2/7 v 3/6 on the way to the semifinals.
    quarterfinals=((0, 7), (3, 4), (2, 5), (1, 6)),
    semifinals=((0, 1), (2, 3)),
)
