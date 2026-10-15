"""Walk-forward picks for both rating sets, mirroring the daily job.

Games kicking off in [D 10:00 UTC, D+1 10:00 UTC) are predicted from ratings fit
on that season's games that kicked off before D 10:00 UTC:
- `season`: this season's games only
- `predictive`: the same, blended with the preseason prior (fades to zero)
"""

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from tsi.db.queries.results import GameResult
from tsi.db.queries.stats import OffenseRow
from tsi.model.blend import BlendParams, predictive_set
from tsi.model.ratings.fit import RatingParams, RatingSet, TeamRating, fit_ratings, predicted_margin

REFIT_HOUR = 10  # UTC, same as the nightly job
ESTABLISHED_GAMES = 4  # provisional threshold (doc 04)


@dataclass(frozen=True)
class Pick:
    game: GameResult
    season_margin: float
    predictive_margin: float
    established: bool  # both teams have 4+ games this season


def refit_day(kickoff: datetime) -> date:
    """The daily run whose ratings a game is predicted from."""
    return (kickoff - timedelta(hours=REFIT_HOUR)).date()


def walk_forward(
    games: Sequence[GameResult],
    grouped_rows: Mapping[int, Sequence[OffenseRow]],
    priors: Mapping[int, Mapping[int, TeamRating]],  # season -> team -> prior
    prior_hfa: float,
    rating_params: RatingParams | None = None,
    blend_params: BlendParams | None = None,
) -> list[Pick]:
    slates: dict[tuple[int, date], list[GameResult]] = defaultdict(list)
    for g in games:
        if g.start_time is not None:
            slates[(g.season, refit_day(g.start_time))].append(g)

    picks = []
    for (season, day), slate in sorted(slates.items()):
        cutoff = datetime.combine(day, time(REFIT_HOUR), tzinfo=UTC)
        known = [r for r in grouped_rows.get(season, ()) if r.start_time and r.start_time < cutoff]
        season_set = fit_ratings(known, rating_params)
        pred_set = predictive_set(season_set, priors.get(season, {}), prior_hfa, blend_params)
        for g in slate:
            played = min(season_set.games.get(g.home_id, 0), season_set.games.get(g.away_id, 0))
            picks.append(
                Pick(g, _margin(season_set, g), _margin(pred_set, g), played >= ESTABLISHED_GAMES)
            )
    return picks


def _margin(ratings: RatingSet, g: GameResult) -> float:
    home, away = ratings.get(g.home_id, g.home_div), ratings.get(g.away_id, g.away_div)
    return predicted_margin(ratings, home, away, g.neutral)
