"""All tunable model settings in one place, so a run can be saved and reproduced."""

from dataclasses import asdict, dataclass, field
from typing import Any

from tsi.model.blend import BlendParams
from tsi.model.ratings.fit import RatingParams

MODEL_VERSION = "tsi-v1.0"


@dataclass(frozen=True)
class ModelConfig:
    rating: RatingParams = field(default_factory=RatingParams)
    blend: BlendParams = field(default_factory=BlendParams)

    def to_dict(self) -> dict[str, Any]:
        return {"version": MODEL_VERSION, **asdict(self)}
