"""Prediction accuracy metrics (doc 04 §9). All inputs are plain sequences."""

import math
from collections.abc import Sequence

EPS = 1e-12  # keeps log loss finite for probabilities of exactly 0 or 1


def mae(pred: Sequence[float], actual: Sequence[float]) -> float:
    return sum(abs(p - a) for p, a in zip(pred, actual, strict=True)) / len(pred)


def rmse(pred: Sequence[float], actual: Sequence[float]) -> float:
    return math.sqrt(sum((p - a) ** 2 for p, a in zip(pred, actual, strict=True)) / len(pred))


def straight_up_accuracy(pred_margin: Sequence[float], actual_margin: Sequence[float]) -> float:
    """Share of games where the predicted winner won. Pick'em predictions count half."""
    score = 0.0
    for p, a in zip(pred_margin, actual_margin, strict=True):
        score += 0.5 if p == 0 or a == 0 else float((p > 0) == (a > 0))
    return score / len(pred_margin)


def brier(prob: Sequence[float], outcome: Sequence[float]) -> float:
    """Mean squared error of win probabilities (outcome 1 = home won). Lower is better."""
    return sum((p - o) ** 2 for p, o in zip(prob, outcome, strict=True)) / len(prob)


def log_loss(prob: Sequence[float], outcome: Sequence[float]) -> float:
    total = 0.0
    for p, o in zip(prob, outcome, strict=True):
        p = min(max(p, EPS), 1 - EPS)
        total -= o * math.log(p) + (1 - o) * math.log(1 - p)
    return total / len(prob)
