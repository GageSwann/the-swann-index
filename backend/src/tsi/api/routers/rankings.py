from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from tsi.api.deps import NowDep, SessionsDep, read, season_or_current
from tsi.services.read.rankings import (
    Division,
    MixedResumeError,
    Rankings,
    RankingType,
    rankings,
)
from tsi.services.read.rankings_top import TopDivision, TopRankings, top_rankings

router = APIRouter(tags=["rankings"])


@router.get("/rankings", response_model=Rankings)
async def get_rankings(
    sessions: SessionsDep,
    now: NowDep,
    season: int | None = None,
    week: int | None = Query(None, description="Latest run within this week (default: latest)."),
    type: RankingType = "power",  # noqa: A002 (the documented query name)
    season_type: Literal["regular", "postseason"] | None = None,
    division: Division = "fbs",
) -> Rankings:
    """Power (how good now) or Résumé (what they've accomplished) rankings.

    `division`: fbs (default), fcs, or all. Ranks are within a division; `all` ranks FBS and
    FCS together by rating (Power only: Résumé benchmarks differ by division, so 422)."""
    try:
        result = await read(
            sessions,
            lambda s: rankings(
                s, season_or_current(season, now), type, week, season_type, division
            ),
        )
    except MixedResumeError as exc:
        raise HTTPException(422, str(exc)) from exc
    if result is None:
        raise HTTPException(404, "No rankings for that season/week yet.")
    return result


@router.get("/rankings/top", response_model=TopRankings)
async def get_top_rankings(
    sessions: SessionsDep,
    now: NowDep,
    division: TopDivision = "fbs",
    n: int = Query(25, ge=1, le=50, description="How many teams per ranking."),
) -> TopRankings:
    """A division's Power and Résumé top `n` from the latest run, with movement since the
    Sunday baseline and records: what the home page's rails show, read cheaply (#155)."""
    result = await read(
        sessions, lambda s: top_rankings(s, season_or_current(None, now), division, n)
    )
    if result is None:
        raise HTTPException(404, "No rankings yet.")
    return result
