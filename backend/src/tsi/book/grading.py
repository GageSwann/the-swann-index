"""Grade a paper pick after the final, and measure closing line value (doc 05 §5).

Spreads are home view (negative = home favored): the home side covers when
margin + line > 0, the away side when margin + line < 0.
CLV (points) = how much better the line taken was than the closing line, from the
picked side's view (> 0 = beat the close). Moneyline CLV is in probability:
closing no-vig probability of the side minus the implied probability taken.
"""

from dataclasses import dataclass

from tsi.book.odds import prob_from_american, profit_per_unit


@dataclass(frozen=True)
class Grade:
    result: str  # 'win' | 'loss' | 'push'
    units_won: float  # flat stake of `stake` units at the odds taken


def grade_pick(
    market: str,
    side: str,
    line: float | None,
    odds: int,
    home_points: int,
    away_points: int,
    stake: float = 1.0,
) -> Grade:
    diff = _cover_diff(market, side, line, home_points, away_points)
    if diff > 0:
        return Grade("win", stake * profit_per_unit(odds))
    if diff < 0:
        return Grade("loss", -stake)
    return Grade("push", 0.0)


def clv_points(market: str, side: str, line_taken: float, closing_line: float) -> float:
    """Spread/total CLV in points from the picked side's view."""
    if market == "spread":
        better = line_taken - closing_line  # home: -3 taken vs. -4.5 close = +1.5
        return better if side == "home" else -better
    if market == "total":
        return closing_line - line_taken if side == "over" else line_taken - closing_line
    raise ValueError(f"no point CLV for market {market!r}")


def clv_prob(odds_taken: int, closing_no_vig_prob: float) -> float:
    """Moneyline CLV: closing fair probability of the side minus what the price taken implied."""
    return closing_no_vig_prob - prob_from_american(odds_taken)


def _cover_diff(
    market: str, side: str, line: float | None, home_points: int, away_points: int
) -> float:
    margin = home_points - away_points
    if market == "ml":
        return margin if side == "home" else -margin
    if line is None:
        raise ValueError(f"{market} pick needs a line")
    if market == "spread":
        return margin + line if side == "home" else -(margin + line)
    total = home_points + away_points
    return total - line if side == "over" else line - total
