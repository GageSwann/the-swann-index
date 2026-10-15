"""Walk-forward report: `season` and `predictive` TSI ratings vs. Elo and the closing line.

Scored set: completed FBS-vs-FBS games with a closing spread, 2015 onward.
Win-probability sigma and prior coefficients are fit on TRAIN seasons only.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from sqlalchemy.orm import Session

from tsi.backtest.evaluate import ScoredGame, Summary, summarize
from tsi.db.queries.market import closing_spreads
from tsi.db.queries.priors import fbs_teams, prior_inputs
from tsi.db.queries.results import completed_games
from tsi.db.queries.stats import offense_rows
from tsi.model.blend import BlendParams
from tsi.model.elo import EloParams
from tsi.model.ratings.fit import RatingParams
from tsi.model.ratings.probability import residual_sigma, win_prob
from tsi.services.elo_report import TRAIN, VALIDATE, elo_picks, is_scored
from tsi.services.prior_setup import build_prior_setup, rows_by_season
from tsi.services.walk_forward import Pick, walk_forward

FIRST_DATA_SEASON = 2014  # supplies 2015's "last season" ratings


@dataclass(frozen=True)
class ComparisonRow:
    season: Summary  # TSI `season` set (this season only)
    predictive: Summary  # TSI `predictive` set (with fading prior)
    elo: Summary


@dataclass(frozen=True)
class RatingsReport:
    rating_params: RatingParams
    blend_params: BlendParams
    prior_hfa: float
    rows: list[ComparisonRow]


def run_ratings_report(
    session: Session,
    through_season: int,
    rating_params: RatingParams | None = None,
    blend_params: BlendParams | None = None,
) -> RatingsReport:
    rating_params = rating_params or RatingParams()
    blend_params = blend_params or BlendParams()
    games = completed_games(session, through_season)
    closing = closing_spreads(session, through_season)
    grouped = rows_by_season(offense_rows(session, FIRST_DATA_SEASON, through_season))
    fbs = fbs_teams(session, FIRST_DATA_SEASON, through_season)
    table = prior_inputs(session, FIRST_DATA_SEASON, through_season)
    _, elo = elo_picks(games, closing, EloParams())

    setup = build_prior_setup(
        grouped, range(FIRST_DATA_SEASON, through_season), fbs, table, TRAIN, rating_params
    )
    scored_seasons = range(TRAIN[0], through_season + 1)
    priors = {s: setup.priors_for(s, fbs.get(s, set()), table) for s in scored_seasons}
    scored_games = [g for g in games if is_scored(g, closing)]
    picks = walk_forward(
        scored_games, grouped, priors, setup.prior_hfa, rating_params, blend_params
    )

    def sigma(margin: Callable[[Pick], float]) -> float:
        train = [p for p in picks if TRAIN[0] <= p.game.season <= TRAIN[1]]
        return residual_sigma([margin(p) for p in train], [p.game.margin for p in train])

    sigmas = {
        "season": sigma(lambda p: p.season_margin),
        "pred": sigma(lambda p: p.predictive_margin),
    }

    def scored(subset: Sequence[Pick], model: str) -> list[ScoredGame]:
        out = []
        for p in subset:
            g = p.game
            if model == "elo":
                margin, prob = elo[g.id].margin, elo[g.id].home_win_prob
            else:
                margin = p.season_margin if model == "season" else p.predictive_margin
                prob = win_prob(margin, sigmas[model])
            out.append(ScoredGame(g.season, margin, prob, g.margin, -closing[g.id]))
        return out

    def row(label: str, subset: Sequence[Pick]) -> ComparisonRow:
        return ComparisonRow(
            *(summarize(label, scored(subset, m)) for m in ("season", "pred", "elo"))
        )

    def in_seasons(first: int, last: int) -> list[Pick]:
        return [p for p in picks if first <= p.game.season <= last]

    validate = in_seasons(*VALIDATE)
    rows = [row(str(s), in_seasons(s, s)) for s in sorted({p.game.season for p in picks})]
    rows += [
        row(f"Train {TRAIN[0]}-{TRAIN[1]}", in_seasons(*TRAIN)),
        row(f"Validate {VALIDATE[0]}-{VALIDATE[1]}", validate),
        row("  both teams 4+ games", [p for p in validate if p.established]),
        row("  provisional (<4)", [p for p in validate if not p.established]),
    ]
    return RatingsReport(rating_params, blend_params, setup.prior_hfa, rows)
