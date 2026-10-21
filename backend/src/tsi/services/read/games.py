"""`/weeks/{season}/{week}/games` (matchup board) and `/games/{id}` (game center).

The snapshot shown is the latest one, or once a game has kicked off, the locked
(latest pre-kickoff) one. The market is the books' consensus as of now, or the
closing consensus once kicked off. Game-center markets (alt ladders, team totals)
are re-priced from the snapshot's stored distribution, so they always match it.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from tsi.book.consensus import ConsensusLine
from tsi.book.pricing import GameMarkets, price_game
from tsi.db.queries.games import GameRow, game_by_id, week_games
from tsi.db.queries.snapshots import SnapshotRow, picks_for_snapshots, snapshots_for_games
from tsi.db.queries.team_info import TeamRef, team_refs
from tsi.divisions import RATED_DIVISION
from tsi.model.distribution import ScoreDistribution
from tsi.services.read.common import (
    Score,
    SnapshotView,
    current_snapshot,
    market_lines,
    result_of,
    snapshot_view,
)


@dataclass(frozen=True)
class GameSummary:
    id: int
    season: int
    week: int
    season_type: str
    kickoff: datetime | None
    kickoff_tbd: bool
    neutral: bool
    conference_game: bool
    notes: str | None
    home: TeamRef
    away: TeamRef
    result: Score | None
    prediction: SnapshotView | None
    market: ConsensusLine | None


@dataclass(frozen=True)
class WeekBoard:
    season: int
    season_type: str
    week: int
    games: list[GameSummary]


@dataclass(frozen=True)
class SnapshotPoint:
    published_at: datetime
    spread: float
    total: float
    home_win_prob: float


@dataclass(frozen=True)
class GameCenter:
    game: GameSummary
    markets: GameMarkets | None  # TSI fair + Book prices, incl. team totals and alt ladders
    history: list[SnapshotPoint]  # every published snapshot, oldest first


def week_board(
    session: Session, season: int, week: int, season_type: str, now: datetime
) -> WeekBoard:
    """Games with at least one FBS team (the rated division); FCS-only games are left out."""
    games = week_games(session, season, week, season_type)
    summaries = _summaries(session, games, now)
    rated = [s for s in summaries if RATED_DIVISION in (s.home.division, s.away.division)]
    return WeekBoard(season, season_type, week, rated)


def game_center(session: Session, game_id: int, now: datetime) -> GameCenter | None:
    game = game_by_id(session, game_id)
    if game is None:
        return None
    all_snaps = snapshots_for_games(session, [game.id])
    summary = _summaries(session, [game], now, all_snaps)[0]
    snaps = all_snaps.get(game.id, [])
    p = summary.prediction
    markets = None if p is None else price_game(_distribution(p))
    history = [SnapshotPoint(s.published_at, s.spread, s.total, s.home_win_prob) for s in snaps]
    return GameCenter(summary, markets, history)


def _summaries(
    session: Session,
    games: list[GameRow],
    now: datetime,
    snaps: dict[int, list[SnapshotRow]] | None = None,  # preloaded, to skip the query
) -> list[GameSummary]:
    if not games:
        return []
    refs = team_refs(session, games[0].season, {t for g in games for t in (g.home_id, g.away_id)})
    if snaps is None:
        snaps = snapshots_for_games(session, [g.id for g in games])
    shown: dict[int, tuple[SnapshotRow, bool]] = {}
    for g in games:
        snap, locked = current_snapshot(snaps.get(g.id, []), g.start_time, now)
        if snap is not None:
            shown[g.id] = (snap, locked)
    picks = picks_for_snapshots(session, [s.id for s, _ in shown.values()])
    markets = market_lines(session, games, now)
    out = []
    for g in games:
        snap = shown.get(g.id)
        out.append(
            GameSummary(
                id=g.id,
                season=g.season,
                week=g.week,
                season_type=g.season_type,
                kickoff=g.start_time,
                kickoff_tbd=g.start_time_tbd,
                neutral=g.neutral,
                conference_game=g.conference_game,
                notes=g.notes,
                home=refs[g.home_id],
                away=refs[g.away_id],
                result=result_of(g),
                prediction=None
                if snap is None
                else snapshot_view(snap[0], snap[1], picks.get(snap[0].id, [])),
                market=markets.get(g.id),
            )
        )
    return out


def _distribution(p: SnapshotView) -> ScoreDistribution:
    return ScoreDistribution(
        margin=p.proj_home - p.proj_away,
        total=p.proj_home + p.proj_away,
        sigma_margin=p.sigma_margin,
        sigma_total=p.sigma_total,
        rho=p.rho,
    )
