"""The fitted production model, saved as a versioned JSON file in the repo.

`tsi model fit` learns everything that is estimated from history (prior model,
stack weights, Elo points scale, win-probability sigmas) on all completed seasons
and writes it here; the daily `tsi rate` job only loads it. Committing the file
makes every live rating reproducible from a git SHA.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from tsi.model.elo import EloParams
from tsi.model.prior import PriorModel
from tsi.model.ratings.fit import RatingParams
from tsi.model.stack import StackModel

ARTIFACT_PATH = Path(__file__).parent / "artifacts" / "current.json"


@dataclass(frozen=True)
class ModelArtifact:
    version: str
    fitted_seasons: tuple[int, int]
    rating: RatingParams
    elo: EloParams  # elo_per_point fitted
    stack: StackModel
    prior: PriorModel
    sigma_predictive: float
    sigma_season: float

    def to_json(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "fitted_seasons": list(self.fitted_seasons),
            "rating": asdict(self.rating),
            "elo": {k: v for k, v in asdict(self.elo).items() if k != "division_means"},
            "stack": {str(b): c.tolist() for b, c in sorted(self.stack.coefs.items())},
            "prior": {
                f"{side}|{','.join(feats)}": c.tolist()
                for (side, feats), c in sorted(self.prior.coefs.items())
            },
            "sigma_predictive": self.sigma_predictive,
            "sigma_season": self.sigma_season,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "ModelArtifact":
        prior = {}
        for key, coef in data["prior"].items():
            side, feats = key.split("|")
            prior[(side, tuple(feats.split(",")) if feats else ())] = np.array(coef)
        return cls(
            version=data["version"],
            fitted_seasons=tuple(data["fitted_seasons"]),
            rating=RatingParams(**data["rating"]),
            elo=EloParams(**data["elo"]),
            stack=StackModel({int(b): np.array(c) for b, c in data["stack"].items()}),
            prior=PriorModel(prior),
            sigma_predictive=data["sigma_predictive"],
            sigma_season=data["sigma_season"],
        )


def save_artifact(artifact: ModelArtifact, path: Path = ARTIFACT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact.to_json(), indent=1) + "\n", encoding="utf-8")


def load_artifact(path: Path = ARTIFACT_PATH) -> ModelArtifact:
    return ModelArtifact.from_json(json.loads(path.read_text(encoding="utf-8")))
