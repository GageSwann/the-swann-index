from pathlib import Path

import numpy as np

from tsi.model.artifact import ModelArtifact, load_artifact, save_artifact
from tsi.model.elo import EloParams
from tsi.model.prior import PriorModel
from tsi.model.ratings.fit import RatingParams
from tsi.model.stack import StackModel


def test_artifact_round_trips_through_json(tmp_path: Path) -> None:
    artifact = ModelArtifact(
        version="tsi-test",
        fitted_seasons=(2015, 2025),
        rating=RatingParams(),
        elo=EloParams(elo_per_point=22.2),
        stack=StackModel({0: np.array([3.0, 1.0, 0.5, 1.1, 0.4]), 6: np.array([1.0] * 5)}),
        prior=PriorModel(
            {
                ("off", ("last", "talent")): np.array([-8.0, 0.4, 0.01]),
                ("defense", ()): np.array([0.0]),
            }
        ),
        sigma_predictive=15.2,
        sigma_season=15.6,
    )
    path = tmp_path / "artifact.json"

    save_artifact(artifact, path)
    loaded = load_artifact(path)

    assert loaded.version == "tsi-test" and loaded.fitted_seasons == (2015, 2025)
    assert loaded.elo.elo_per_point == 22.2
    np.testing.assert_allclose(loaded.stack.coefs[6], artifact.stack.coefs[6])
    np.testing.assert_allclose(loaded.prior.coefs[("off", ("last", "talent"))], [-8.0, 0.4, 0.01])
    assert ("defense", ()) in loaded.prior.coefs


def test_committed_artifact_loads() -> None:
    artifact = load_artifact()

    assert artifact.version.startswith("tsi-v") and set(artifact.stack.coefs) == set(range(7))
