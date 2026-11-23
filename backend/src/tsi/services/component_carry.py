"""Build last season's saved component fit, and decide whether a live run may use it.

A live run takes last season's fit from the committed carry (model/component_carry.py)
only when the database still holds exactly the stat rows it was fitted on: the
database computes a fingerprint of them (~32 bytes) instead of sending the season's
rows (~0.5 MB). Anything else (no file, another season, another ridge penalty or model
version, a changed stat row) fits last season from the database as before, so live
results never depend on the shortcut.
"""

import logging

from sqlalchemy.orm import Session

from tsi.db.queries.stats import offense_rows, offense_rows_fingerprint
from tsi.model.component_carry import ComponentCarry, load_carry
from tsi.model.ratings.components import Components, fit_components

logger = logging.getLogger(__name__)


def build_component_carry(
    session: Session, season: int, lam: float, model_version: str
) -> ComponentCarry | None:
    """Fit `season` exactly as live runs do; None when the season has no usable rows."""
    components = fit_components(offense_rows(session, season, season), lam)
    if components is None:
        return None
    return ComponentCarry(
        through_season=season,
        fingerprint=offense_rows_fingerprint(session, season),
        lam=lam,
        model_version=model_version,
        components=components,
    )


def last_season_components(
    session: Session,
    season: int,
    lam: float,
    model_version: str,
    carry: ComponentCarry | None = None,
) -> Components | None:
    """Last season's final fit: from the saved carry when it still holds, else fitted."""
    carry = carry or load_carry()
    if carry is not None and carry.usable(season, lam, model_version):
        if offense_rows_fingerprint(session, season - 1) == carry.fingerprint:
            return carry.components
        logger.warning(
            "saved component fit of %s no longer matches the stats; fitting it again "
            "(rebuild it with `tsi model carry`)",
            carry.through_season,
        )
    return fit_components(offense_rows(session, season - 1, season - 1), lam)
