"""One projected bracket from the playoff odds: a valid field under the format's rules.

The simulated fields differ from season to season, so the page shows a single
representative one: each power conference's likeliest champion, the group-of-six team
likeliest to make it, the independent if it's among the twelve likeliest, then at-large
teams by playoff odds. Seeds go by each team's average seed when it makes the field.
The FCS version (#125) works the same way with the FCS auto bids and 8 seeds.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from tsi.sim.cfp_format import CfpFormat
from tsi.sim.fcs_format import FcsFormat


@dataclass(frozen=True)
class OddsRow:
    team_id: int
    slug: str
    conference: str | None
    playoff_prob: float
    conference_title_prob: float | None
    seed_dist: Sequence[float]  # P(seed = 1..field size)

    @property
    def mean_seed(self) -> float:
        """Average seed when in the field (field size + 1 if it never is)."""
        if self.playoff_prob <= 0:
            return len(self.seed_dist) + 1.0
        return sum((s + 1) * p for s, p in enumerate(self.seed_dist)) / self.playoff_prob


def projected_field(rows: Sequence[OddsRow], fmt: CfpFormat) -> list[OddsRow]:
    """The projected field, best seed first."""
    # Teams that never made a simulated field can't be in the projected one.
    by_odds = sorted(
        (r for r in rows if r.playoff_prob > 0), key=lambda r: (-r.playoff_prob, r.team_id)
    )
    field: list[OddsRow] = []

    def add(row: OddsRow | None) -> None:
        if row is not None and row not in field:
            field.append(row)

    for conf in fmt.champion_bids:
        members = [r for r in by_odds if r.conference == conf and r.conference_title_prob]
        add(max(members, key=lambda r: (r.conference_title_prob, r.playoff_prob), default=None))
    add(next((r for r in by_odds if r.conference in fmt.group_bid_conferences), None))
    if fmt.independent_bid is not None:
        slug, best = fmt.independent_bid
        add(next((r for r in by_odds[:best] if r.slug == slug), None))
    for r in by_odds:
        if len(field) >= fmt.field_size:
            break
        add(r)
    return sorted(field, key=lambda r: (r.mean_seed, -r.playoff_prob))


def projected_fcs_field(rows: Sequence[OddsRow], fmt: FcsFormat) -> list[OddsRow]:
    """The projected FCS field by position: each auto-bid conference's likeliest champion
    that can go, then at-large teams by playoff odds; the 8 likeliest to be seeded are the
    seeds (ordered by their average seed), the rest follow by playoff odds."""
    by_odds = sorted(
        (r for r in rows if r.playoff_prob > 0), key=lambda r: (-r.playoff_prob, r.team_id)
    )
    field: list[OddsRow] = []
    for conf in fmt.champion_bids:
        members = [r for r in by_odds if r.conference == conf and r.conference_title_prob]
        best = max(members, key=lambda r: (r.conference_title_prob, r.playoff_prob), default=None)
        if best is not None and best not in field:
            field.append(best)
    field += [r for r in by_odds if r not in field][: max(fmt.field_size - len(field), 0)]
    seeded = sorted(field, key=lambda r: (-sum(r.seed_dist), r.team_id))[: fmt.seeds]
    seeded.sort(key=lambda r: (_mean_seed_if_seeded(r), -r.playoff_prob))
    rest = sorted((r for r in field if r not in seeded), key=lambda r: (-r.playoff_prob, r.team_id))
    return seeded + rest


def _mean_seed_if_seeded(r: OddsRow) -> float:
    p = sum(r.seed_dist)
    return sum((s + 1) * q for s, q in enumerate(r.seed_dist)) / p if p > 0 else 99.0
