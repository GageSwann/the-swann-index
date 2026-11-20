"""Rebuilt forecasts (#152): which games have any forecast, and rebuilt rows as snapshots."""

from collections.abc import Iterable, Sequence
from datetime import datetime

from sqlalchemy import exists, select, union
from sqlalchemy.orm import Session

from tsi.db.models import ModelRun, Prediction, RebuiltForecast, TeamRating
from tsi.db.queries.filters import one_of


def published_game_ids(session: Session, game_ids: Sequence[int]) -> set[int]:
    """Games with at least one published snapshot."""
    query = select(Prediction.game_id).where(one_of(Prediction.game_id, game_ids)).distinct()
    return set(session.scalars(query))


def forecast_game_ids(session: Session, game_ids: Sequence[int]) -> set[int]:
    """Games with a published snapshot or a rebuilt forecast."""
    query = union(
        select(Prediction.game_id).where(one_of(Prediction.game_id, game_ids)),
        select(RebuiltForecast.game_id).where(one_of(RebuiltForecast.game_id, game_ids)),
    )
    return set(session.scalars(query))


REBUILT_COLUMNS = (
    RebuiltForecast.game_id,
    RebuiltForecast.as_of,
    RebuiltForecast.proj_home,
    RebuiltForecast.proj_away,
    RebuiltForecast.spread,
    RebuiltForecast.total,
    RebuiltForecast.home_win_prob,
    RebuiltForecast.sigma_margin,
    RebuiltForecast.sigma_total,
    RebuiltForecast.rho,
    RebuiltForecast.fair_home_ml,
    RebuiltForecast.fair_away_ml,
    RebuiltForecast.book_home_ml,
    RebuiltForecast.book_away_ml,
    RebuiltForecast.book_spread_home_odds,
    RebuiltForecast.book_spread_away_odds,
    RebuiltForecast.book_over_odds,
    RebuiltForecast.book_under_odds,
    RebuiltForecast.variant,
    RebuiltForecast.adjustment_ids,
)


def rebuilt_rows(session: Session, game_ids: Iterable[int]) -> list:
    """Rebuilt rows of these games, official (adjusted) first within a game."""
    query = (
        select(*REBUILT_COLUMNS)
        .where(one_of(RebuiltForecast.game_id, list(game_ids)))
        .order_by(RebuiltForecast.game_id, RebuiltForecast.variant)  # 'adjusted' < 'raw'
    )
    return list(session.execute(query))


def run_ratings(session: Session, run_id: int) -> dict[tuple[int, str], tuple]:
    """(team, basis) -> the stored rating values a replay must reproduce (`verify`)."""
    query = select(
        TeamRating.team_id,
        TeamRating.basis,
        TeamRating.rating,
        TeamRating.off_rating,
        TeamRating.def_rating,
        TeamRating.rank_power,
        TeamRating.sor,
        TeamRating.rank_resume,
    ).where(TeamRating.run_id == run_id, TeamRating.variant == "raw")
    out = {}
    for team_id, basis, *values in session.execute(query):
        out[(team_id, basis)] = tuple(values) if basis == "season" else tuple(values[:3])
    return out


def raw_published_at(session: Session, published_at: datetime) -> dict[int, tuple]:
    """game -> (proj_home, proj_away, home_win_prob) of raw rows published at that moment."""
    query = select(
        Prediction.game_id, Prediction.proj_home, Prediction.proj_away, Prediction.home_win_prob
    ).where(Prediction.published_at == published_at, Prediction.variant == "raw")
    return {game_id: tuple(values) for game_id, *values in session.execute(query)}


def run_time(session: Session, run_id: int) -> datetime | None:
    return session.scalar(select(ModelRun.run_at).where(ModelRun.id == run_id))


def latest_rating_run_id(session: Session, season: int) -> int | None:
    """The newest real (not rebuilt) nightly rating run: the one `verify` replays."""
    query = (
        select(ModelRun.id)
        .where(
            ModelRun.kind == "live",
            ModelRun.season == season,
            ModelRun.params["job"].astext.is_(None),
            exists().where(TeamRating.run_id == ModelRun.id),
        )
        .order_by(ModelRun.run_at.desc(), ModelRun.id.desc())
        .limit(1)
    )
    return session.scalar(query)
