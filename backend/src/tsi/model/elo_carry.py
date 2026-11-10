"""Elo state at the end of a finished season, saved so live runs don't replay history.

Live runs need Elo ratings carried over from every season since 2014, but finished
seasons never change, so their end state is computed once (`tsi model elo-carry`)
and committed next to the artifact. A live run resumes from it and replays only the
current season. The file holds a fingerprint of the exact games it was built from;
the run uses it only when the database still fingerprints the same, and the Elo
parameters match, so the result is identical to a full replay (else it replays all).
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tsi.model.elo import EloParams, EloRun

ELO_CARRY_PATH = Path(__file__).parent / "artifacts" / "elo_carry.json"


@dataclass(frozen=True)
class EloCarry:
    through_season: int  # last season replayed
    fingerprint: str  # of the games replayed (db.queries.results.completed_games_fingerprint)
    params: Mapping[str, Any]  # the Elo parameters that move ratings
    run: EloRun  # end state (ratings, divisions, season); no predictions

    def usable(self, season: int, params: EloParams) -> bool:
        """A start for `season`: built through the season before, with the same params."""
        return self.through_season == season - 1 and dict(self.params) == rating_params(params)


def rating_params(params: EloParams) -> dict[str, Any]:
    """The parameters that change ratings (not `elo_per_point`, which only scales margins)."""
    return {
        "k": params.k,
        "hfa": params.hfa,
        "carryover": params.carryover,
        "division_means": dict(params.division_means),
    }


def carry_to_json(carry: EloCarry) -> dict[str, Any]:
    # JSON floats round-trip exactly (repr), so a resumed run matches a full replay.
    return {
        "through_season": carry.through_season,
        "fingerprint": carry.fingerprint,
        "params": dict(carry.params),
        "season": carry.run.season,
        "ratings": {str(t): r for t, r in sorted(carry.run.ratings.items())},
        "divisions": {str(t): d for t, d in sorted(carry.run.divisions.items())},
    }


def carry_from_json(data: Mapping[str, Any]) -> EloCarry:
    return EloCarry(
        through_season=int(data["through_season"]),
        fingerprint=str(data["fingerprint"]),
        params=dict(data["params"]),
        run=EloRun(
            predictions=[],
            ratings={int(t): float(r) for t, r in data["ratings"].items()},
            divisions={int(t): str(d) for t, d in data["divisions"].items()},
            season=data["season"],
        ),
    )


def save_carry(carry: EloCarry, path: Path = ELO_CARRY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(carry_to_json(carry), indent=1) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def load_carry(path: Path = ELO_CARRY_PATH) -> EloCarry | None:
    """The committed carry, or None when there is none."""
    if not path.exists():
        return None
    return carry_from_json(json.loads(path.read_text(encoding="utf-8")))
