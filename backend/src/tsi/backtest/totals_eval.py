"""Score predicted game totals against results and the closing over/under."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from tsi.backtest.walk_forward import Pick


@dataclass(frozen=True)
class TotalsSummary:
    label: str
    games: int
    mae: float  # TSI total vs. actual
    market_mae: float  # closing total vs. actual
    bias: float  # mean (TSI - actual); > 0 means TSI projects too many points
    ou_accuracy: float  # share of non-push games where TSI picked the right side of the close


def summarize_totals(
    label: str, picks: Sequence[Pick], closing: Mapping[int, float]
) -> TotalsSummary:
    """Only games with a closing total are scored."""
    rows = [
        (p.predictive_total, float(p.game.home_points + p.game.away_points), closing[p.game.id])
        for p in picks
        if p.game.id in closing
    ]
    if not rows:
        return TotalsSummary(label, 0, 0.0, 0.0, 0.0, 0.0)
    n = len(rows)
    graded = [(pred > line) == (actual > line) for pred, actual, line in rows if actual != line]
    return TotalsSummary(
        label=label,
        games=n,
        mae=sum(abs(pred - actual) for pred, actual, _ in rows) / n,
        market_mae=sum(abs(line - actual) for _, actual, line in rows) / n,
        bias=sum(pred - actual for pred, actual, _ in rows) / n,
        ou_accuracy=sum(graded) / len(graded) if graded else 0.0,
    )
