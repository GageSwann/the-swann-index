"""All tunable model settings in one place, so a run can be saved and reproduced."""

from dataclasses import asdict, dataclass, field
from typing import Any

from tsi.model.ratings.fit import RatingParams
from tsi.model.stack import DEFAULT_LAM

MODEL_VERSION = "tsi-v1.2"  # v1.1: season blend + stacked margin; v1.2: + stacked totals
ESTABLISHED_GAMES = 4  # fewer games played -> provisional rank (doc 04)


@dataclass(frozen=True)
class ModelConfig:
    rating: RatingParams = field(default_factory=RatingParams)
    stack_lam: float = DEFAULT_LAM  # ridge penalty on the predictive stack weights

    def to_dict(self) -> dict[str, Any]:
        return {"version": MODEL_VERSION, **asdict(self)}
