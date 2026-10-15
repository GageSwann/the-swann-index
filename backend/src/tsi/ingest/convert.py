"""Tolerant converters for CFBD values (numbers sometimes arrive as strings or null)."""

from typing import Any


def to_float(value: Any) -> float | None:
    """'1634.04' -> 1634.04; None/'' or junk -> None."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int | None:
    """'2024' -> 2024; None or junk -> None."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
