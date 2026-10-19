"""Compute today's live ratings for the current season (what the nightly job stores).

- `season` set + Power/Résumé ranks: services/rankings.py (this season only)
- `predictive` set: the stack, expressed per team (model/stack_team.py), using the
  production artifact (prior model, stack weights, Elo scale)
Only data from games that kicked off before `now` is used.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from tsi.db.queries.priors import fbs_teams, prior_inputs
from tsi.db.queries.results import completed_games
from tsi.db.queries.stats import offense_rows
from tsi.ingest.freshness import current_season
from tsi.model.artifact import ModelArtifact
from tsi.model.config import ESTABLISHED_GAMES
from tsi.model.elo import run_elo
from tsi.model.ratings.components import fit_components
from tsi.model.ratings.fit import fit_ratings
from tsi.model.ratings.types import AVERAGE_TEAM, TeamRating
from tsi.model.stack import stage_bucket
from tsi.model.stack_team import TeamSignals, predictive_hfa, predictive_rating
from tsi.services.prior_setup import prior_inputs_for
from tsi.services.rankings import Rankings, build_rankings


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


def compute_live_ratings(session: Session, now: datetime, artifact: ModelArtifact) -> LiveRatings:
    season = current_season(now)
    rankings = build_rankings(session, season, now, artifact.rating, artifact.sigma_season)

    rows = [r for r in offense_rows(session, season, season) if r.start_time and r.start_time < now]
    components = fit_components(rows, artifact.rating.lam)
    last_final = fit_ratings(offense_rows(session, season - 1, season - 1), artifact.rating)
    table = prior_inputs(session, season, season)
    fbs = fbs_teams(session, season, season).get(season, set())
    priors = {
        t: artifact.prior.predict(prior_inputs_for(season, t, {season - 1: last_final}, table))
        for t in fbs
    }

    games = [g for g in completed_games(session, season) if g.start_time and g.start_time < now]
    elo = run_elo(games, artifact.elo).ratings
    fbs_elo = [elo[t] for t in fbs if t in elo]
    elo_mean = sum(fbs_elo) / len(fbs_elo) if fbs_elo else 1500.0

    played = components.games if components else {}
    teams = []
    for t in sorted(fbs):
        signals = TeamSignals(
            ppd=components.ppd.teams.get(t, AVERAGE_TEAM) if components else AVERAGE_TEAM,
            success=(
                components.success.teams.get(t, AVERAGE_TEAM)
                if components and components.success
                else AVERAGE_TEAM
            ),
            prior=priors.get(t, AVERAGE_TEAM),
            elo_points=(elo.get(t, elo_mean) - elo_mean) / artifact.elo.elo_per_point,
        )
        n = played.get(t, 0)
        rating = predictive_rating(artifact.stack, stage_bucket(n), signals)
        teams.append(PredictiveTeam(t, rating, n, n < ESTABLISHED_GAMES))

    typical = sorted(played.values())[len(played) // 2] if played else 0
    hfa = predictive_hfa(
        artifact.stack, stage_bucket(typical), artifact.elo.hfa / artifact.elo.elo_per_point
    )
    return LiveRatings(season, now, rankings, teams, hfa)
