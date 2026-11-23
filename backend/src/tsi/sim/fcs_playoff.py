"""FCS playoff field and bracket in every simulated season (decision #125).

Field: the auto-bid holders, then the best-ranked eligible teams (the committee stand-in's
order) until 24; positions follow that order, so positions 1-16 are the seeds. Bracket
(sim/fcs_format.py): seeded and better-placed teams host until the neutral-site final.
Game means come from the published model (the caller's `mean_margin`, cached per
pairing) plus both teams' shifts from the same simulation and fresh game noise.
Team values are whatever indexes the caller uses (the simulation's own). Once the real
bracket is set (#157), `KnownGames` holds what is already decided: finished games keep
their winner, and scheduled games are played at their real site.
"""

from dataclasses import dataclass

import numpy as np

from tsi.sim.bracket import MeanMargin
from tsi.sim.fcs_format import FcsFormat
from tsi.sim.season import SimulatedGames


def fcs_field(
    order: np.ndarray, bids: np.ndarray, eligible: np.ndarray, fmt: FcsFormat
) -> np.ndarray | None:
    """(sims, field_size) teams by position (column 0 = the 1 seed), or None if too few
    teams are eligible. `order`: (sims, teams) best first; `bids`: (sims, conferences) the
    team holding each automatic bid, -1 for none."""
    sims, teams = order.shape
    if eligible.sum() < fmt.field_size:
        return None
    rows = np.arange(sims)[:, None]
    auto = np.zeros((sims, teams + 1), dtype=bool)  # the extra column absorbs "-1: no bid"
    auto[rows, np.where(bids >= 0, bids, teams)] = True
    auto = auto[:, :teams] & eligible[None, :]
    open_spots = fmt.field_size - auto.sum(axis=1, keepdims=True)
    auto_in_order = auto[rows, order]
    candidate = ~auto_in_order & eligible[order]
    at_large = candidate & (np.cumsum(candidate, axis=1) <= open_spots)
    return order[auto_in_order | at_large].reshape(sims, fmt.field_size)


Pair = tuple[int, int]  # two teams, lower index first


@dataclass(frozen=True)
class KnownGames:
    winners: dict[Pair, int]  # finished games: pair -> the winner
    sites: dict[Pair, tuple[int, bool]]  # scheduled or finished: pair -> (home, neutral)


@dataclass(frozen=True)
class FcsBracket:
    field: np.ndarray  # (sims, 24) team per position
    second_round: np.ndarray  # (sims, 16) teams that reach it (8 byes + 8 winners)
    quarterfinalists: np.ndarray  # (sims, 8)
    semifinalists: np.ndarray  # (sims, 4)
    finalists: np.ndarray  # (sims, 2)
    champion: np.ndarray  # (sims,)


def play_fcs_bracket(
    field: np.ndarray,
    sim: SimulatedGames,
    mean_margin: MeanMargin,
    fmt: FcsFormat,
    known: KnownGames | None = None,
) -> FcsBracket:
    """`sim.shift` is indexed by the same team values as `field`."""
    cache: dict[tuple[int, int, bool], float] = {}
    rows = np.arange(field.shape[0])

    def mean(a: int, b: int, neutral: bool) -> float:
        key = (a, b, neutral)
        if key not in cache:
            cache[key] = mean_margin(a, b, neutral)
        return cache[key]

    def play(a, b, neutral: bool = False):
        """a, b: (team, position) arrays; the better position (lower number) hosts."""
        (ta, pa), (tb, pb) = a, b
        a_hosts = pa < pb
        host, guest = np.where(a_hosts, ta, tb), np.where(a_hosts, tb, ta)
        at_neutral = np.full(len(rows), neutral)
        decided = None
        if known is not None:
            host, guest, at_neutral, decided = _apply_known(host, guest, at_neutral, known)
        pairs = zip(host.tolist(), guest.tolist(), at_neutral.tolist(), strict=True)
        means = np.array([mean(h, g, n) for h, g, n in pairs])
        margin = means + sim.shift[rows, host] - sim.shift[rows, guest]
        margin += sim.rng.normal(0.0, sim.noise, len(rows))
        host_won = margin > 0
        winner = np.where(host_won, host, guest)
        if decided is not None:
            winner = np.where(decided >= 0, decided, winner)
        return winner, np.where(winner == ta, pa, pb)

    def slot(position: int):
        return field[:, position - 1], np.full(len(rows), position)

    first = [play(slot(hi), slot(lo)) for hi, lo in fmt.first_round]
    second_teams = [(slot(s), first[g]) for s, g in fmt.second_round]
    second = [play(a, b) for a, b in second_teams]
    quarters = [play(second[i], second[j]) for i, j in fmt.quarterfinals]
    semis = [play(quarters[i], quarters[j]) for i, j in fmt.semifinals]
    champion, _ = play(semis[0], semis[1], neutral=True)
    return FcsBracket(
        field=field,
        second_round=np.stack([t for pair in second_teams for t, _ in pair], axis=1),
        quarterfinalists=np.stack([t for t, _ in second], axis=1),
        semifinalists=np.stack([t for t, _ in quarters], axis=1),
        finalists=np.stack([t for t, _ in semis], axis=1),
        champion=champion,
    )


def _apply_known(
    host: np.ndarray, guest: np.ndarray, neutral: np.ndarray, known: KnownGames
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """The real site of scheduled pairings, and the winner of finished ones (-1: not
    decided). Looked up once per distinct pairing, not per simulated season."""
    lo, hi = np.minimum(host, guest), np.maximum(host, guest)
    pairs, inverse = np.unique(np.stack([lo, hi], axis=1), axis=0, return_inverse=True)
    inverse = inverse.reshape(-1)
    keys = [(int(a), int(b)) for a, b in pairs]
    site_home = np.array([known.sites.get(k, (-1, False))[0] for k in keys])[inverse]
    site_neutral = np.array([known.sites.get(k, (-1, False))[1] for k in keys])[inverse]
    decided = np.array([known.winners.get(k, -1) for k in keys])[inverse]
    scheduled = site_home >= 0
    new_host = np.where(scheduled, site_home, host)
    new_guest = np.where(scheduled & (site_home == guest), host, guest)
    return new_host, new_guest, np.where(scheduled, site_neutral, neutral), decided
