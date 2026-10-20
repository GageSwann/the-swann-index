"""TSI Book settings: how much vig to charge and how wide the alt ladders run (doc 05 §2)."""

from dataclasses import dataclass

STANDARD_HOLD = 1 / 22  # -110 / -110


@dataclass(frozen=True)
class BookConfig:
    line_hold: float = STANDARD_HOLD  # spreads, totals, team totals, alt ladders
    moneyline_hold: float = 0.045
    main_line_odds: int | None = -110  # flat price on main lines; None = price from probability
    ladder_width: float = 10.0  # alt lines run main line +- this many points
    ladder_step: float = 1.0
