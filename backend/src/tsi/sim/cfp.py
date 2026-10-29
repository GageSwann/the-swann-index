"""Playoff field and seeds in every simulated season, from the simulated committee ranking.

Automatic bids (sim/cfp_format.py): the named conferences' champions, the highest-ranked
team from the group-bid conferences, and the independent (Notre Dame) when ranked high
enough. At-large bids fill the field in ranking order. Seeds follow the ranking, so the
top four ranked teams are the top four seeds (they're always in, as at-large if needed).
"""

from dataclasses import dataclass

import numpy as np

from tsi.sim.cfp_format import CfpFormat


@dataclass(frozen=True)
class FieldInputs:
    champions: np.ndarray  # (sims, len(champion_bids)) team index of each champion
    group_members: np.ndarray  # (teams,) bool: in a group-bid conference
    independent: int | None  # team index of the independent with a bid rule


def seeds(order: np.ndarray, inputs: FieldInputs, fmt: CfpFormat) -> np.ndarray:
    """(sims, field_size): team index at each seed (column 0 = the 1 seed)."""
    sims, teams = order.shape
    rows = np.arange(sims)[:, None]
    rank = np.empty_like(order)
    rank[rows, order] = np.arange(teams)  # 0 = best

    auto = np.zeros((sims, teams), dtype=bool)
    auto[rows, inputs.champions] = True
    group_rank = np.where(inputs.group_members[None, :], rank, teams)
    auto[np.arange(sims), group_rank.argmin(axis=1)] = True
    if inputs.independent is not None and fmt.independent_bid is not None:
        best = fmt.independent_bid[1]
        auto[:, inputs.independent] |= rank[:, inputs.independent] < best

    # At-large: the best-ranked teams without an automatic bid fill the open spots.
    open_spots = fmt.field_size - auto.sum(axis=1, keepdims=True)
    auto_in_order = auto[rows, order]
    at_large_in_order = ~auto_in_order & (np.cumsum(~auto_in_order, axis=1) <= open_spots)
    in_field = auto_in_order | at_large_in_order
    return order[in_field].reshape(sims, fmt.field_size)
