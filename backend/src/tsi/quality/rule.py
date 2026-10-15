"""A data quality rule: a SQL query returning one row per problem, (season, detail)."""

from dataclasses import dataclass
from typing import Literal

Severity = Literal["fail", "warn"]


@dataclass(frozen=True)
class Check:
    name: str
    severity: Severity
    description: str
    sql: str  # takes :season (NULL = all seasons)
