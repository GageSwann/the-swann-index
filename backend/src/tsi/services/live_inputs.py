"""Everything a live run needs as of a moment: the same pieces the backtest uses per slate.

Only games that kicked off before `as_of` are used (rule 1). Shared by the daily
ratings (`services/rate.py`) and game predictions (`services/predict.py`) so the
two can never disagree about their inputs.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from tsi.db.queries.priors import fbs_teams, prior_inputs
from tsi.db.queries.results import completed_games
from tsi.db.queries.stats import offense_rows
from tsi.model.artifact import ModelArtifact
from tsi.model.elo import EloRun, run_elo
from tsi.model.ratings.components import Components, fit_components
from tsi.model.ratings.fit import AVERAGE, blend_components
from tsi.model.ratings.types import TeamRating
from tsi.services.prior_setup import prior_inputs_for


@dataclass(frozen=True)
class LiveInputs:
    season: int
    as_of: datetime
    components: Components | None  # this season's games before `as_of`
    last_components: Components | None  # last season's final fit
    priors: dict[int, TeamRating]  # FBS team -> preseason prior
    elo: EloRun  # every completed game before `as_of`, all seasons
    fbs: set[int]

    def games_played(self, team_id: int) -> int:
        return self.components.games.get(team_id, 0) if self.components else 0


def load_live_inputs(
    session: Session, season: int, as_of: datetime, artifact: ModelArtifact
) -> LiveInputs:
    lam = artifact.rating.lam
    rows = [
        r for r in offense_rows(session, season, season) if r.start_time and r.start_time < as_of
    ]
    last_components = fit_components(offense_rows(session, season - 1, season - 1), lam)
    last_final = (
        AVERAGE if last_components is None else blend_components(last_components, artifact.rating)
    )
    table = prior_inputs(session, season, season)
    fbs = fbs_teams(session, season, season).get(season, set())
    priors = {
        t: artifact.prior.predict(prior_inputs_for(season, t, {season - 1: last_final}, table))
        for t in fbs
    }
    games = [g for g in completed_games(session, season) if g.start_time and g.start_time < as_of]
    return LiveInputs(
        season=season,
        as_of=as_of,
        components=fit_components(rows, lam),
        last_components=last_components,
        priors=priors,
        elo=run_elo(games, artifact.elo),
        fbs=fbs,
    )
