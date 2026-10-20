"""Probability <-> American odds (doc 05 §2), and the bookmaker's hold.

    p >= 0.5:  odds = -100 * p / (1 - p)
    p <  0.5:  odds = +100 * (1 - p) / p
A two-way market with hold h is priced at implied probabilities p / (1 - h) per
side, so they add up to 1 / (1 - h). Standard -110 / -110 is a hold of 1/22
(4.55%): 0.5 / (1 - 1/22) = 0.5238 = 110 / 210.
"""

PROB_FLOOR = 0.0005  # caps prices near +/-200000 instead of dividing by zero
MAX_IMPLIED = 0.995  # a vigged favorite never costs more than -19900


def american_from_prob(p: float) -> int:
    p = min(max(p, PROB_FLOOR), 1 - PROB_FLOOR)
    if p >= 0.5:
        return -round(100 * p / (1 - p))
    return round(100 * (1 - p) / p)


def prob_from_american(odds: int) -> float:
    """Implied probability of a price (includes the vig if the price has one)."""
    if odds < 0:
        return -odds / (-odds + 100)
    return 100 / (odds + 100)


def vigged_american(p: float, hold: float) -> int:
    """The Book's price for a side TSI gives probability `p`, charging `hold`."""
    return american_from_prob(min(p / (1 - hold), MAX_IMPLIED))


def profit_per_unit(odds: int) -> float:
    """Units won on a 1-unit winning bet at `odds`."""
    return 100 / -odds if odds < 0 else odds / 100
