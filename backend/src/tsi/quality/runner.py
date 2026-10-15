"""Run the quality checks and summarize results."""

from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.orm import Session

from tsi.quality.checks import CHECKS, Check

MAX_EXAMPLES = 5


@dataclass(frozen=True)
class CheckResult:
    check: Check
    count: int
    by_season: dict[int, int] = field(default_factory=dict)
    examples: list[str] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return self.check.severity == "fail" and self.count > 0


def run_checks(session: Session, season: int | None = None) -> list[CheckResult]:
    results = []
    for check in CHECKS:
        rows = session.execute(text(check.sql), {"season": season}).all()
        results.append(
            CheckResult(
                check=check,
                count=len(rows),
                by_season=dict(sorted(Counter(int(r[0]) for r in rows).items())),
                examples=[f"{r[0]}: {r[1]}" for r in rows[:MAX_EXAMPLES]],
            )
        )
    return results
