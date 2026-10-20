"""Predict upcoming games from live inputs: the backtest's per-game math, applied to today.

For each game: stacking features (model/features.py) -> margin and total stacks
from the artifact -> bivariate-normal score distribution. Mirrors
`backtest/walk_forward.py` exactly (same features, same stage bucket), so the
backtest measures what is published.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from tsi.db.queries.schedule import UpcomingGame
from tsi.model.artifact import ModelArtifact
from tsi.model.distribution import ScoreDistribution
from tsi.model.features import GameSide, margin_features, total_features
from tsi.model.ratings.design import rated_id
from tsi.model.stack import stage_bucket
from tsi.services.live_inputs import LiveInputs


@dataclass(frozen=True)
class GameForecast:
    game: UpcomingGame
    bucket: int  # season stage (fewer games played of the two teams)
    distribution: ScoreDistribution


def forecast_games(
    games: Sequence[UpcomingGame], live: LiveInputs, artifact: ModelArtifact
) -> list[GameForecast]:
    return [forecast_game(g, live, artifact) for g in games]


def forecast_game(g: UpcomingGame, live: LiveInputs, artifact: ModelArtifact) -> GameForecast:
    side = GameSide(rated_id(g.home_id, g.home_div), rated_id(g.away_id, g.away_div), g.neutral)
    bucket = stage_bucket(min(live.games_played(g.home_id), live.games_played(g.away_id)))
    elo_margin = live.elo.margin(
        artifact.elo, g.season, (g.home_id, g.home_div), (g.away_id, g.away_div), g.neutral
    )
    margin = artifact.stack.predict(
        bucket, margin_features(side, live.components, live.priors, elo_margin)
    )
    total = artifact.totals.predict(
        bucket, total_features(side, live.components, live.last_components, live.priors)
    )
    return GameForecast(g, bucket, artifact.distribution.for_game(margin, total))
