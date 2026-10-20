"""Fit the production model on every completed season and build the artifact.

Same pipeline as the backtest (walk-forward features, so the stack learns from
honest pre-kickoff inputs), but every estimated piece is fit on ALL completed
seasons instead of only TRAIN: validation is finished, so production should
learn from the most data.
"""

from sqlalchemy.orm import Session

from tsi.backtest.elo_picks import elo_picks
from tsi.backtest.market_calibration import fit_edge_shrink, spread_samples, total_samples
from tsi.backtest.splits import FIRST_SCORED_SEASON
from tsi.backtest.stacking import fit_margin_stack, fit_total_stack, stacked_picks
from tsi.backtest.walk_forward import walk_forward
from tsi.db.queries.market import closing_spreads
from tsi.db.queries.results import completed_games
from tsi.model.artifact import ModelArtifact
from tsi.model.config import MODEL_VERSION, ModelConfig
from tsi.model.distribution_fit import fit_distribution
from tsi.model.elo import EloParams
from tsi.model.ratings.probability import fit_sigma
from tsi.services.backtest_data import FIRST_DATA_SEASON, load_backtest_data
from tsi.services.prior_setup import build_prior_setup


def fit_production_model(
    session: Session, last_completed_season: int, config: ModelConfig | None = None
) -> ModelArtifact:
    config = config or ModelConfig()
    seasons = (FIRST_SCORED_SEASON, last_completed_season)
    data = load_backtest_data(session, last_completed_season)
    games = completed_games(session, last_completed_season)
    elo_params, elo = elo_picks(
        games, closing_spreads(session, last_completed_season), EloParams(), seasons
    )

    setup = build_prior_setup(
        data.rows,
        range(FIRST_DATA_SEASON, last_completed_season + 1),
        data.fbs,
        data.prior_table,
        seasons,
        config.rating,
    )
    priors = {
        s: setup.priors_for(s, data.fbs.get(s, set()), data.prior_table)
        for s in range(seasons[0], seasons[1] + 1)
    }
    picks = walk_forward(
        data.scored_games,
        data.rows,
        priors,
        config.rating,
        {gid: pick.margin for gid, pick in elo.items()},
        setup.final_components,
    )
    # Distribution and edge shrink are fit on leave-one-season-out stack predictions:
    # in-sample predictions look sharper than live ones and would overstate edges.
    held_out = stacked_picks(picks, config.stack_lam, seasons)
    margins = [p.predictive_margin for p in held_out]
    actual = [p.game.margin for p in held_out]
    distribution = fit_distribution(
        fit_sigma(margins, actual),
        margins,
        actual,
        [p.predictive_total for p in held_out],
        [p.game.home_points + p.game.away_points for p in held_out],
    )
    established = [p for p in picks if p.established]
    return ModelArtifact(
        version=MODEL_VERSION,
        fitted_seasons=seasons,
        rating=config.rating,
        elo=elo_params,
        stack=fit_margin_stack(picks, config.stack_lam),
        totals=fit_total_stack(picks, config.stack_lam),
        prior=setup.model,
        distribution=distribution,
        edge_shrink=fit_edge_shrink(
            spread_samples(held_out, distribution, {g: o.spread for g, o in data.opening.items()}),
            total_samples(held_out, distribution, {g: o.total for g, o in data.opening.items()}),
        ),
        sigma_season=fit_sigma(
            [p.season_margin for p in established], [p.game.margin for p in established]
        ),
    )
