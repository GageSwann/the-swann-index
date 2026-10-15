"""Sanity check: TSI end-of-season `season` ratings vs. SP+ final ratings (doc 04 §12).

SP+ history from CFBD is end-of-season only, so this compares FINAL ratings
(not predictions). SP+ is never a model input. Responses are cached on disk
forever once a season is over (~1 CFBD call per season, first time only).
"""

from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.backtest.compare import Agreement, compare_ratings
from tsi.db.models import Team
from tsi.db.queries.stats import offense_rows
from tsi.ingest.client import CfbdClient
from tsi.model.ratings.design import POOLED_ID
from tsi.model.ratings.fit import fit_ratings


@dataclass(frozen=True)
class SeasonAgreement:
    season: int
    agreement: Agreement
    names: dict[int, str]


def compare_with_sp(
    client: CfbdClient, session: Session, seasons: Iterable[int]
) -> list[SeasonAgreement]:
    team_ids = {school: tid for tid, school in session.execute(select(Team.id, Team.school))}
    names = {tid: school for school, tid in team_ids.items()}
    results = []
    for season in seasons:
        ours = fit_ratings(offense_rows(session, season, season))
        ours_rating = {t: r.rating for t, r in ours.teams.items() if t != POOLED_ID}
        sp = {
            team_ids[row["team"]]: float(row["rating"])
            for row in client.get("/ratings/sp", {"year": season})
            if row.get("team") in team_ids and row.get("rating") is not None
        }
        results.append(SeasonAgreement(season, compare_ratings(ours_rating, sp), names))
    return results
