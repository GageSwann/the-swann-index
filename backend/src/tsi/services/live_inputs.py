"""Everything a live run needs as of a moment: the same pieces the backtest uses per slate.

Only games that kicked off before `as_of` are used (rule 1). Shared by the daily
ratings (`services/rate.py`) and game predictions (`services/predict.py`) so the
two can never disagree about their inputs. The operator's manual adjustments in
effect at `as_of` ride along for the predictions; the ratings never read them (rule 6).
"""

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from tsi.db.queries.adjustments import StoredAdjustment, season_adjustments
from tsi.db.queries.priors import division_teams, fbs_teams, prior_inputs
from tsi.db.queries.results import completed_games
from tsi.db.queries.schedule import team_kickoffs
from tsi.db.queries.stats import offense_rows
from tsi.divisions import FCS, FCS_STATS_FROM
from tsi.model.artifact import ModelArtifact
from tsi.model.elo import EloRun, run_elo
from tsi.model.ratings.components import Components, fit_components
from tsi.model.ratings.fit import AVERAGE, blend_components
from tsi.model.ratings.types import TeamRating
from tsi.model.situational import features as situational_features
from tsi.model.situational import rest_days
from tsi.services.elo_carry import starting_elo
from tsi.services.prior_setup import prior_inputs_for


@dataclass(frozen=True)
class LiveInputs:
    season: int
    as_of: datetime
    components: Components | None  # this season's games before `as_of`
    last_components: Components | None  # last season's final fit
    priors: dict[int, TeamRating]  # FBS (and from 2022 FCS) team -> preseason prior
    elo: EloRun  # every completed game before `as_of`, all seasons (may resume, #146)
    fbs: set[int]
    fcs: frozenset[int] = frozenset()  # individually rated FCS teams this season (#109)
    adjustments: tuple[StoredAdjustment, ...] = ()  # in effect at `as_of` (decision #104)
    kickoffs: dict[int, list[datetime]] = field(default_factory=dict)  # team -> season (#120)

    def games_played(self, team_id: int) -> int:
        return self.components.games.get(team_id, 0) if self.components else 0

    def situation(self, home: int, away: int, kickoff: datetime) -> tuple[float, float, float]:
        """Rest / bye / short-week features of a scheduled game (model/situational.py)."""
        rest = [rest_days(self.kickoffs.get(t, ()), kickoff) for t in (home, away)]
        return situational_features(*rest)


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
    fcs: dict[int, set[int]] = {}
    if season >= FCS_STATS_FROM:  # FCS teams are rated individually (decision #109)
        fcs = division_teams(session, season - 1, season, FCS)
        priors |= artifact.fcs_prior.priors(
            fcs.get(season, set()), last_final, fcs.get(season - 1, set())
        )
    # Elo carries over from every past season: resume from the saved end of last season
    # when it still matches the database (one season read), else replay them all (#146).
    start = starting_elo(session, season, artifact.elo)
    games = [
        g
        for g in completed_games(session, season, from_season=season if start else None)
        if g.start_time and g.start_time < as_of
    ]
    return LiveInputs(
        season=season,
        as_of=as_of,
        components=fit_components(rows, lam),
        last_components=last_components,
        priors=priors,
        elo=run_elo(games, artifact.elo, start),
        fbs=fbs,
        fcs=frozenset(fcs.get(season, set())),
        kickoffs={team: k for (team, _), k in team_kickoffs(session, season, season).items()},
        adjustments=tuple(
            a for a in season_adjustments(session, season, open_at=as_of) if a.created_at <= as_of
        ),
    )
