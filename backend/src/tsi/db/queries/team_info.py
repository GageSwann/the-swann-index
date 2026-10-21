"""Team display info, stored ratings, and win-loss records for read pages."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from tsi.db.models import Game, Team, TeamRating, TeamSeason


@dataclass(frozen=True)
class TeamRef:
    id: int
    slug: str
    school: str
    abbreviation: str | None
    mascot: str | None
    color: str | None
    alt_color: str | None
    logo_url: str | None
    conference: str | None
    division: str | None


@dataclass(frozen=True)
class StoredRating:
    team_id: int
    basis: str  # 'season' | 'predictive'
    rating: float
    off_rating: float
    def_rating: float
    games_played: int
    provisional: bool
    rank_power: int | None
    rank_resume: int | None
    sor: float | None


@dataclass(frozen=True)
class Record:
    wins: int = 0
    losses: int = 0
    ties: int = 0


def team_refs(
    session: Session,
    season: int,
    team_ids: Iterable[int] | None = None,
    division: str | None = None,
) -> dict[int, TeamRef]:
    """Teams with their conference/division in `season` (left join: teams without a row too)."""
    query = select(
        Team.id,
        Team.slug,
        Team.school,
        Team.abbreviation,
        Team.mascot,
        Team.color,
        Team.alt_color,
        Team.logo_url,
        TeamSeason.conference,
        TeamSeason.division,
    ).outerjoin(TeamSeason, (TeamSeason.team_id == Team.id) & (TeamSeason.season == season))
    if team_ids is not None:
        query = query.where(Team.id.in_(list(team_ids)))
    if division is not None:
        query = query.where(TeamSeason.division == division)
    return {row[0]: TeamRef(*row) for row in session.execute(query)}


def team_id_by_slug(session: Session, slug: str) -> int | None:
    return session.scalar(select(Team.id).where(Team.slug == slug))


def stored_ratings(
    session: Session, run_ids: Iterable[int], team_id: int | None = None
) -> dict[int, list[StoredRating]]:
    """run id -> its raw ratings (both bases), optionally for one team."""
    query = select(
        TeamRating.run_id,
        TeamRating.team_id,
        TeamRating.basis,
        TeamRating.rating,
        TeamRating.off_rating,
        TeamRating.def_rating,
        TeamRating.games_played,
        TeamRating.provisional,
        TeamRating.rank_power,
        TeamRating.rank_resume,
        TeamRating.sor,
    ).where(TeamRating.run_id.in_(list(run_ids)), TeamRating.variant == "raw")
    if team_id is not None:
        query = query.where(TeamRating.team_id == team_id)
    out: dict[int, list[StoredRating]] = defaultdict(list)
    for run_id, *rest in session.execute(query):
        out[run_id].append(StoredRating(*rest))
    return out


def records(session: Session, season: int, before: datetime) -> dict[int, Record]:
    """Win-loss records of every team from games completed and kicked off before `before`."""
    query = select(Game.home_id, Game.away_id, Game.home_points, Game.away_points).where(
        Game.season == season,
        Game.completed,
        Game.home_points.is_not(None),
        Game.start_time < before,
    )
    tally: dict[int, list[int]] = defaultdict(lambda: [0, 0, 0])
    for home, away, hp, ap in session.execute(query):
        if hp == ap:
            tally[home][2] += 1
            tally[away][2] += 1
        else:
            winner, loser = (home, away) if hp > ap else (away, home)
            tally[winner][0] += 1
            tally[loser][1] += 1
    return {team: Record(*t) for team, t in tally.items()}
