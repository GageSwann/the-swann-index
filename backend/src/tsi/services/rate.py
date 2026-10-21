"""Compute today's live ratings for the current season (what the nightly job stores).

- `season` set + Power/Résumé ranks: services/compute_rankings.py (this season only)
- `predictive` set: the stack, expressed per team (model/stack_team.py), using the
  production artifact (prior model, stack weights, Elo scale)
Only data from games that kicked off before `now` is used.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

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
    rankings = build_rankings(session, season, now, artifact.rating, artifact.sigma_season)
    live = inputs or load_live_inputs(session, season, now, artifact)
    components = live.components

    elo = live.elo.ratings
    fbs_elo = [elo[t] for t in live.fbs if t in elo]
    elo_mean = sum(fbs_elo) / len(fbs_elo) if fbs_elo else 1500.0

    teams = []
    for t in sorted(live.fbs):
        signals = TeamSignals(
            ppd=components.ppd.teams.get(t, AVERAGE_TEAM) if components else AVERAGE_TEAM,
            success=(
                components.success.teams.get(t, AVERAGE_TEAM)
                if components and components.success
                else AVERAGE_TEAM
            ),
            prior=live.priors.get(t, AVERAGE_TEAM),
            elo_points=(elo.get(t, elo_mean) - elo_mean) / artifact.elo.elo_per_point,
        )
        n = live.games_played(t)
        rating = predictive_rating(artifact.stack, stage_bucket(n), signals)
        teams.append(PredictiveTeam(t, rating, n, n < ESTABLISHED_GAMES))

    played = components.games if components else {}
    typical = sorted(played.values())[len(played) // 2] if played else 0
    hfa = predictive_hfa(
        artifact.stack, stage_bucket(typical), artifact.elo.hfa / artifact.elo.elo_per_point
    )
    return LiveRatings(season, now, rankings, teams, hfa)
