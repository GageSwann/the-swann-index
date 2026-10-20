"""Build preseason priors: final ratings per season -> prior model -> each season's priors.

No look-ahead: season Y's priors use only season Y-1's final ratings plus Y's
preseason talent and returning production. Prior coefficients are fit on the
TRAIN target seasons only (so validation seasons are out-of-sample).
"""

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from tsi.db.queries.priors import PriorRow
from tsi.db.queries.stats import OffenseRow
from tsi.model.prior import PriorInputs, PriorModel, fit_prior_model
from tsi.model.ratings.components import Components, fit_components
from tsi.model.ratings.fit import AVERAGE, RatingParams, RatingSet, TeamRating, blend_components

InputsTable = Mapping[tuple[int, int], PriorRow]


@dataclass(frozen=True)
class PriorSetup:
    model: PriorModel
    finals: dict[int, RatingSet]  # completed seasons' end-of-season `season` ratings
    final_components: dict[int, Components | None]  # same fits, per component (totals)

    def priors_for(
        self, season: int, teams: Iterable[int], table: InputsTable
    ) -> dict[int, TeamRating]:
        return {
            t: self.model.predict(prior_inputs_for(season, t, self.finals, table)) for t in teams
        }


def rows_by_season(rows: Iterable[OffenseRow]) -> dict[int, list[OffenseRow]]:
    grouped: dict[int, list[OffenseRow]] = defaultdict(list)
    for r in rows:
        grouped[r.season].append(r)
    return grouped


def build_prior_setup(
    grouped: Mapping[int, Sequence[OffenseRow]],
    completed_seasons: Iterable[int],
    fbs: Mapping[int, set[int]],
    table: InputsTable,
    train: tuple[int, int],
    params: RatingParams | None = None,
) -> PriorSetup:
    params = params or RatingParams()
    components = {
        s: fit_components(grouped[s], params.lam) for s in completed_seasons if s in grouped
    }
    finals = {
        s: AVERAGE if c is None else blend_components(c, params) for s, c in components.items()
    }
    samples = [
        (prior_inputs_for(season, team, finals, table), finals[season].teams[team])
        for season in range(train[0], train[1] + 1)
        if season in finals
        for team in fbs.get(season, set()) & set(finals[season].teams)
    ]
    return PriorSetup(fit_prior_model(samples), finals, components)


def prior_inputs_for(
    season: int, team: int, finals: Mapping[int, RatingSet], table: InputsTable
) -> PriorInputs:
    """Preseason inputs for one team: last season's final rating + this season's table row."""
    last_season = finals.get(season - 1)
    last = last_season.teams.get(team) if last_season else None
    row = table.get((season, team), PriorRow())
    return PriorInputs(
        last=last,
        talent=row.talent,
        returning=row.returning,
        returning_passing=row.returning_passing,
        recruiting=row.recruiting,
        portal=row.portal,
        new_coach=row.new_coach,
    )
