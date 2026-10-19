"""Team-level `predictive` ratings from the stack (for storage and display).

The stack predicts a game margin from home-minus-away differences:
    margin = c_site*site + c_ppd*dPPD + c_success*dSuccess + c_prior*dPrior + c_elo*eloMargin
Each difference is (home value - away value), so a team's predictive rating at a
given stage is just its own weighted sum, and margins between two teams at the
same stage are reproduced exactly:
    rating = c_ppd*PPD + c_success*Success + c_prior*Prior + c_elo*(Elo / pts_per_elo)
Elo has no offense/defense split, so its share is split evenly. Home field =
c_site plus Elo's own home-field term scaled by c_elo.
"""

from dataclasses import dataclass

from tsi.model.ratings.types import TeamRating
from tsi.model.stack import FEATURES, StackModel


@dataclass(frozen=True)
class TeamSignals:
    ppd: TeamRating
    success: TeamRating
    prior: TeamRating
    elo_points: float  # (Elo rating - FBS mean) / Elo per point


def _coefs(model: StackModel, bucket: int) -> dict[str, float]:
    coef = model.coefs.get(bucket)
    if coef is None:
        coef = model.coefs[min(model.coefs, key=lambda b: abs(b - bucket))]
    return dict(zip(FEATURES, (float(c) for c in coef), strict=True))


def predictive_rating(model: StackModel, bucket: int, s: TeamSignals) -> TeamRating:
    c = _coefs(model, bucket)
    half_elo = c["elo"] * s.elo_points / 2
    return TeamRating(
        off=c["ppd"] * s.ppd.off
        + c["success"] * s.success.off
        + c["prior"] * s.prior.off
        + half_elo,
        defense=c["ppd"] * s.ppd.defense
        + c["success"] * s.success.defense
        + c["prior"] * s.prior.defense
        + half_elo,
    )


def predictive_hfa(model: StackModel, bucket: int, elo_hfa_points: float) -> float:
    c = _coefs(model, bucket)
    return c["site"] + c["elo"] * elo_hfa_points
