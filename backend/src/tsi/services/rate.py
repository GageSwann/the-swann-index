"""Compute today's live ratings for the current season (what the nightly job stores).

- `season` set + Power/Résumé ranks: services/compute_rankings.py (this season only)
- `predictive` set: the stack, expressed per team (model/stack_team.py), using the
  production artifact (prior model, stack weights, Elo scale)
Only data from games that kicked off before `now` is used.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from tsi.divisions import FCS, RATED_DIVISION
from tsi.ingest.freshness import current_season
from tsi.model.artifact import ModelArtifact
from tsi.model.config import ESTABLISHED_GAMES
from tsi.model.ratings.types import AVERAGE_TEAM, TeamRating
from tsi.model.stack import stage_bucket
from tsi.model.stack_team import TeamSignals, predictive_hfa, predictive_rating
from tsi.services.compute_rankings import Rankings, build_rankings
from tsi.services.live_inputs import LiveInputs, load_live_inputs


@dataclass(frozen=True)
class PredictiveTeam:
    team_id: int
    rating: TeamRating
    games: int
    provisional: bool
    division: str = RATED_DIVISION  # ranked within its division


@dataclass(frozen=True)
class LiveRatings:
    season: int
    as_of: datetime
    rankings: Rankings
    predictive: list[PredictiveTeam]
    predictive_hfa: float


def compute_live_ratings(
    session: Session,
    now: datetime,
    artifact: ModelArtifact,
    inputs: LiveInputs | None = None,
) -> LiveRatings:
    season = current_season(now)
    live = inputs or load_live_inputs(session, season, now, artifact)
    rankings = build_rankings(
        session, season, now, artifact.rating, artifact.sigma_season, live=live
    )
    components = live.components

    elo = live.elo.ratings
    fbs_elo = [elo[t] for t in live.fbs if t in elo]
    elo_mean = sum(fbs_elo) / len(fbs_elo) if fbs_elo else 1500.0

    teams = []
    division_of = {t: RATED_DIVISION for t in live.fbs} | {t: FCS for t in live.fcs}

    def component(metric, team: int) -> TeamRating:
        return metric.teams.get(team, AVERAGE_TEAM) if metric else AVERAGE_TEAM

    for t in [*sorted(live.fbs), *sorted(live.fcs)]:
        signals = TeamSignals(
            ppd=component(components.ppd if components else None, t),
            success=component(components.success if components else None, t),
            prior=live.priors.get(t, AVERAGE_TEAM),
            elo_points=(elo.get(t, elo_mean) - elo_mean) / artifact.elo.elo_per_point,
            second=component(components.second if components else None, t),
            power=component(components.power if components else None, t),
        )
        n = live.games_played(t)
        rating = predictive_rating(artifact.stack, stage_bucket(n), signals)
        teams.append(PredictiveTeam(t, rating, n, n < ESTABLISHED_GAMES, division_of[t]))

    # FBS teams only: the typical stage of an FBS game sets the predictive home field.
    played = {t: n for t, n in (components.games if components else {}).items() if t in live.fbs}
    typical = sorted(played.values())[len(played) // 2] if played else 0
    hfa = predictive_hfa(
        artifact.stack, stage_bucket(typical), artifact.elo.hfa / artifact.elo.elo_per_point
    )
    return LiveRatings(season, now, rankings, teams, hfa)
