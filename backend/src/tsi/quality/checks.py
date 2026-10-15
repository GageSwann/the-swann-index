"""All data quality rules (doc 03), in report order: `fail` rules first, then `warn`."""

from tsi.quality.fail_rules import FAIL_RULES
from tsi.quality.rule import Check, Severity
from tsi.quality.warn_rules import WARN_RULES

CHECKS: tuple[Check, ...] = FAIL_RULES + WARN_RULES

__all__ = ["CHECKS", "Check", "Severity"]
