"""Walk-forward picks for both rating sets, mirroring the daily job.

Games kicking off in [D 10:00 UTC, D+1 10:00 UTC) are predicted from ratings fit
on that season's games that kicked off before D 10:00 UTC:
- `season` margin: this season's games only (the rankings' ratings)
- stacking features for the `predictive` margin and total (model/features.py), all pre-kickoff
"""

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from tsi.db.queries.results import GameResult
from tsi.db.queries.stats import OffenseRow
from tsi.model.config import ESTABLISHED_GAMES
from tsi.model.features import GameSide, margin_features, total_features
from tsi.model.ratings.components import Components, fit_components
from tsi.model.ratings.design import rated_id
from tsi.model.ratings.fit import AVERAGE, RatingParams, blend_components, predicted_margin
from tsi.model.ratings.types import RatingSet, TeamRating
from tsi.model.stack import stage_bucket

REFIT_HOUR = 10  # UTC, same as the nightly job


@dataclass(frozen=True)
class Pick:
    game: GameResult
    season_margin: float
    predictive_margin: float  # filled in by the stack (services/backtest.py)
    predictive_total: float  # filled in by the totals stack
    established: bool  # both teams have 4+ games this season
    bucket: int  # stacking stage (fewer games played of the two teams)
    features: tuple[float, ...]  # margin stack features, model/stack.FEATURES order
    total_features: tuple[float, ...]  # model/totals.TOTAL_FEATURES order


def refit_day(kickoff: datetime) -> date:
    """The daily run whose ratings a game is predicted from."""
    return (kickoff - timedelta(hours=REFIT_HOUR)).date()


def walk_forward(
    games: Sequence[GameResult],
    grouped_rows: Mapping[int, Sequence[OffenseRow]],
    priors: Mapping[int, Mapping[int, TeamRating]],  # season -> team -> prior
    rating_params: RatingParams | None = None,
    elo_margins: Mapping[int, float] | None = None,  # game_id -> Elo margin (pre-game)
    finals: Mapping[int, Components | None] | None = None,  # season -> final components
) -> list[Pick]:
    rating_params = rating_params or RatingParams()
    elo_margins = elo_margins or {}
    finals = finals or {}
    slates: dict[tuple[int, date], list[GameResult]] = defaultdict(list)
    for g in games:
        if g.start_time is not None:
            slates[(g.season, refit_day(g.start_time))].append(g)

    picks = []
    for (season, day), slate in sorted(slates.items()):
        cutoff = datetime.combine(day, time(REFIT_HOUR), tzinfo=UTC)
        known = [r for r in grouped_rows.get(season, ()) if r.start_time and r.start_time < cutoff]
        components = fit_components(known, rating_params.lam)
        season_set = AVERAGE if components is None else blend_components(components, rating_params)
        season_priors = priors.get(season, {})
        last = finals.get(season - 1)
        for g in slate:
            played = min(season_set.games.get(g.home_id, 0), season_set.games.get(g.away_id, 0))
            season_margin = _margin(season_set, g)
            side = GameSide(
                rated_id(g.home_id, g.home_div), rated_id(g.away_id, g.away_div), g.neutral
            )
            picks.append(
                Pick(
                    game=g,
                    season_margin=season_margin,
                    predictive_margin=season_margin,
                    predictive_total=0.0,
                    established=played >= ESTABLISHED_GAMES,
                    bucket=stage_bucket(played),
                    features=margin_features(
                        side, components, season_priors, elo_margins.get(g.id, 0.0)
                    ),
                    total_features=total_features(side, components, last, season_priors),
                )
            )
    return picks


def _margin(ratings: RatingSet, g: GameResult) -> float:
    home, away = ratings.get(g.home_id, g.home_div), ratings.get(g.away_id, g.away_div)
    return predicted_margin(ratings, home, away, g.neutral)
