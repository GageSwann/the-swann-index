"""Last season's fitted components, saved so live runs don't read last season's stats.

Every live run needs last season's final component fit (the preseason prior and the
totals stack's last pace/tempo), which meant reading the whole season's team-game stats
(~0.5 MB of Neon transfer a night) to fit numbers that never change once the season is
over. Like the Elo carry (model/elo_carry.py, #146), the fit is computed once
(`tsi model carry`) and committed next to the artifact. A run uses it only when it was
built for the season before, with the same ridge penalty and model version, and the
database still fingerprints the same stat rows; otherwise it fits as before, so the
result is identical either way.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tsi.model.ratings.components import Components, MetricRatings
from tsi.model.ratings.types import TeamRating

COMPONENT_CARRY_PATH = Path(__file__).parent / "artifacts" / "component_carry.json"
METRICS = ("ppd", "success", "pace", "tempo", "second", "power")  # Components' fit fields


@dataclass(frozen=True)
class ComponentCarry:
    through_season: int  # the season fitted
    fingerprint: str  # of its stat rows (db.queries.stats.offense_rows_fingerprint)
    lam: float  # ridge penalty of the fit
    model_version: str  # artifact version it was built under (fitting code changes bump it)
    components: Components

    def usable(self, season: int, lam: float, model_version: str) -> bool:
        """Last season's fit for `season`, made the way this model would make it."""
        return (
            self.through_season == season - 1
            and self.lam == lam
            and self.model_version == model_version
        )


def carry_to_json(carry: ComponentCarry) -> dict[str, Any]:
    # JSON floats round-trip exactly (repr), so a run using it matches a fresh fit.
    c = carry.components
    return {
        "through_season": carry.through_season,
        "fingerprint": carry.fingerprint,
        "lam": carry.lam,
        "model_version": carry.model_version,
        # The fit's own key order (JSON keeps it), so iterating a loaded dict matches too.
        "games": {str(t): n for t, n in c.games.items()},
        **{name: _metric_to_json(getattr(c, name)) for name in METRICS},
    }


def carry_from_json(data: Mapping[str, Any]) -> ComponentCarry:
    metrics = {name: _metric_from_json(data[name]) for name in METRICS}
    if metrics["ppd"] is None or metrics["pace"] is None:
        raise ValueError("component carry lacks the ppd or pace fit")
    return ComponentCarry(
        through_season=int(data["through_season"]),
        fingerprint=str(data["fingerprint"]),
        lam=float(data["lam"]),
        model_version=str(data["model_version"]),
        components=Components(games={int(t): int(n) for t, n in data["games"].items()}, **metrics),
    )


def save_carry(carry: ComponentCarry, path: Path = COMPONENT_CARRY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(carry_to_json(carry), indent=1) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def load_carry(path: Path = COMPONENT_CARRY_PATH) -> ComponentCarry | None:
    """The committed carry, or None when there is none."""
    if not path.exists():
        return None
    return carry_from_json(json.loads(path.read_text(encoding="utf-8")))


def _metric_to_json(metric: MetricRatings | None) -> dict[str, Any] | None:
    if metric is None:
        return None
    return {
        "hfa": metric.hfa,
        "level": metric.level,
        "teams": {str(t): [r.off, r.defense] for t, r in metric.teams.items()},
    }


def _metric_from_json(data: Mapping[str, Any] | None) -> MetricRatings | None:
    if data is None:
        return None
    return MetricRatings(
        teams={int(t): TeamRating(float(o), float(d)) for t, (o, d) in data["teams"].items()},
        hfa=float(data["hfa"]),
        level=float(data["level"]),
    )
