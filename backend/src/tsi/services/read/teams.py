"""`/teams` and `/teams/{slug}`: team list, and a team's profile, rating history and schedule."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from tsi.db.queries.adjustments import season_adjustments
from tsi.db.queries.games import GameRow, team_games
from tsi.db.queries.runs import latest_rating_run, rating_history
from tsi.db.queries.sim import stored_outlooks, stored_sims
from tsi.db.queries.snapshots import current_snapshots
from tsi.db.queries.team_info import (
    Record,
    StoredRating,
    TeamRef,
    stored_ratings,
    tally_records,
    team_id_by_slug,
    team_refs,
)
from tsi.db.queries.venues import game_venues
from tsi.divisions import LISTED_DIVISIONS, RATED_DIVISION, rated_individually
from tsi.services.read.common import AdjustmentNote, note_of, result_of
from tsi.services.read.game_card import GameCard, game_card, team_records
from tsi.services.read.games import game_summaries
from tsi.services.read.projection import Projection, projection
from tsi.services.read.resume_cache import ResumeCache
from tsi.services.read.resume_view import (
    ResumeSummary,
    resume_context,
    resume_summary,
)
from tsi.services.read.schedule_view import ScheduleGame, schedule_game


@dataclass(frozen=True)
class TeamRatings:
    rating: float
    off_rating: float
    def_rating: float
    rank_power: int | None
    rank_resume: int | None
    sor: float | None
    sos: float | None
    games_played: int
    provisional: bool
    predictive_rating: float | None
    predictive_rank: int | None


@dataclass(frozen=True)
class RatingPoint:
    as_of: datetime
    week: int
    rating: float
    rank_power: int | None
    rank_resume: int | None
    predictive_rating: float | None


@dataclass(frozen=True)
class TeamProfile:
    team: TeamRef
    season: int
    wins: int
    losses: int
    ties: int
    ratings: TeamRatings | None
    history: list[RatingPoint]
    schedule: list[ScheduleGame]
    resume: ResumeSummary | None  # None for unrated teams or before ratings exist
    projection: Projection | None  # season sim of the shown run (#98); FBS teams only
    adjustments: list[AdjustmentNote]  # manual adjustments in effect now (decision #104)
    # Conference record (title games excluded, #190); None for independents (#199).
    conf_record: Record | None = None
    # The next game not yet final, as the Game of the Week card shows it; once the season's
    # games are all final, the last one played (#199). None without games.
    next_game: GameCard | None = None


def team_list(session: Session, season: int, division: str = RATED_DIVISION) -> list[TeamRef]:
    """Teams of a division ("all": every listed division) that season, by name."""
    divisions = LISTED_DIVISIONS if division == "all" else (division,)
    teams = [t for d in divisions for t in team_refs(session, season, division=d).values()]
    return sorted(teams, key=lambda t: t.school)


def team_profile(
    session: Session,
    slug: str,
    season: int,
    now: datetime,
    contexts: ResumeCache | None = None,  # the API's shared one (#148); None: build it here
) -> TeamProfile | None:
    team_id = team_id_by_slug(session, slug)
    if team_id is None:
        return None
    games = team_games(session, season, team_id)
    refs = team_refs(
        session, season, {team_id} | {g.home_id for g in games} | {g.away_id for g in games}
    )
    latest = latest_rating_run(session, season)
    latest_rows = stored_ratings(session, [latest.id], team_id).get(latest.id, []) if latest else []
    # Same rule as `records()`: completed, scored and kicked off before now.
    finished = [
        (g.home_id, g.away_id, g.home_points, g.away_points)
        for g in games
        if g.completed and g.home_points is not None and g.start_time and g.start_time < now
    ]
    rec = tally_records(finished).get(team_id, Record())
    snaps = current_snapshots(session, [g.id for g in games], now)
    division = refs[team_id].division or ""
    rated = rated_individually(division, season)  # FBS, and FCS from 2022 (#109)
    # Résumé breakdown vs. the team's own division benchmark (#12 FBS, #24 FCS; #114, #133).
    run_ctx = None
    if latest and rated:
        run_ctx = contexts.get(session, latest) if contexts else resume_context(session, latest)
    ctx = run_ctx.for_division(division) if run_ctx else None
    # FBS and FCS teams (#125); D-II and below aren't simulated.
    sim = stored_sims(session, latest.id, team_id).get(team_id) if latest and rated else None
    upcoming = [g.id for g in games if not g.completed]
    outlooks = stored_outlooks(session, latest.id, upcoming) if latest and upcoming else {}
    # The next game's card, and both teams' records as of now, like the header's (#199).
    shown = _next_game(games)
    recs = team_records(
        session,
        season,
        now,
        {team_id} | ({shown.home_id, shown.away_id} if shown else set()),
    )
    card = None
    if shown is not None:
        summary = game_summaries(session, [shown], now, {shown.id: snaps.get(shown.id, [])}, refs)
        card = game_card(summary[0], recs, game_venues(session, [shown.id]).get(shown.id))
    return TeamProfile(
        team=refs[team_id],
        season=season,
        wins=rec.wins,
        losses=rec.losses,
        ties=rec.ties,
        ratings=_ratings(latest_rows) if latest and rated else None,
        history=[
            RatingPoint(
                h.run_at, h.week, h.rating, h.rank_power, h.rank_resume, h.predictive_rating
            )
            for h in (rating_history(session, season, team_id) if rated else [])
            if h.rating is not None  # runs without a season rating (the first days) are skipped
        ],
        schedule=[
            schedule_game(g, team_id, refs, snaps.get(g.id, []), now, ctx, outlooks.get(g.id))
            for g in games
        ],
        resume=resume_summary(ctx, games, team_id, refs) if ctx else None,
        projection=projection(sim),
        adjustments=[
            note_of(a)
            for a in season_adjustments(session, season, open_at=now)
            if a.team_id == team_id and a.created_at <= now
        ],
        conf_record=recs.conference_of(refs[team_id]),
        next_game=card,
    )


def _next_game(games: list[GameRow]) -> GameRow | None:
    """The first game by kickoff that isn't final yet (one in progress counts); when every
    game is final, the last one played."""
    by_kickoff = sorted(games, key=lambda g: (g.start_time is None, g.start_time, g.id))
    for g in by_kickoff:
        result = result_of(g)
        if result is None or not result.final:
            return g
    return by_kickoff[-1] if by_kickoff else None


def _ratings(rows: list[StoredRating]) -> TeamRatings | None:
    season = next((r for r in rows if r.basis == "season"), None)
    if season is None:
        return None
    pred = next((r for r in rows if r.basis == "predictive"), None)
    return TeamRatings(
        rating=season.rating,
        off_rating=season.off_rating,
        def_rating=season.def_rating,
        rank_power=season.rank_power,
        rank_resume=season.rank_resume,
        sor=season.sor,
        sos=season.sos,
        games_played=season.games_played,
        provisional=season.provisional,
        predictive_rating=pred.rating if pred else None,
        predictive_rank=pred.rank_power if pred else None,
    )
