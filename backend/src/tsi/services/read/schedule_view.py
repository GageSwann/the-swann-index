"""One game on a team page's schedule: result, TSI's view, and its Résumé difficulty."""

from dataclasses import dataclass
from datetime import datetime

from tsi.db.queries.games import GameRow
from tsi.db.queries.snapshots import SnapshotRow
from tsi.db.queries.team_info import TeamRef
from tsi.services.read.common import Score, current_snapshot, result_of
from tsi.services.read.resume_view import ResumeContext, game_difficulty


@dataclass(frozen=True)
class ScheduleGame:
    game_id: int
    kickoff: datetime | None
    week: int
    season_type: str
    opponent: TeamRef
    site: str  # 'home' | 'away' | 'neutral'
    result: Score | None  # home/away points as played
    team_points: int | None
    opponent_points: int | None
    outcome: str | None  # 'W' | 'L' | 'T' once final
    projected_team: float | None  # TSI projection, latest (or locked) snapshot
    projected_opponent: float | None
    win_prob: float | None  # TSI win probability for this team
    spread: float | None  # TSI spread from this team's view (negative = favored)
    adjusted: bool  # the prediction above includes manual adjustments (decision #104)
    # Résumé breakdown (decision #89), from the shown rating run:
    opponent_rating: float | None  # opponent's current `season` rating
    opponent_rank: int | None  # current Power rank, if in the team's own division
    benchmark_win_prob: float | None  # chance the benchmark (#12 FBS / #10 FCS) wins it
    in_resume: bool  # counts toward the Résumé (decided before the run)


def schedule_game(
    g: GameRow,
    team_id: int,
    refs: dict[int, TeamRef],
    snaps: list[SnapshotRow],
    now: datetime,
    ctx: ResumeContext | None,
) -> ScheduleGame:
    home = g.home_id == team_id
    sign = 1 if home else -1
    opponent = refs[g.away_id if home else g.home_id]
    result = result_of(g)
    team_pts = opp_pts = outcome = None
    if result is not None:
        team_pts, opp_pts = (
            (result.home_points, result.away_points)
            if home
            else (result.away_points, result.home_points)
        )
        if result.final:
            outcome = "W" if team_pts > opp_pts else "L" if team_pts < opp_pts else "T"
    snap, _ = current_snapshot(snaps, g.start_time, now)
    diff = game_difficulty(ctx, g, team_id, opponent) if ctx else None
    return ScheduleGame(
        game_id=g.id,
        kickoff=g.start_time,
        week=g.week,
        season_type=g.season_type,
        opponent=opponent,
        site="neutral" if g.neutral else "home" if home else "away",
        result=result,
        team_points=team_pts,
        opponent_points=opp_pts,
        outcome=outcome,
        projected_team=None if snap is None else (snap.proj_home if home else snap.proj_away),
        projected_opponent=None if snap is None else (snap.proj_away if home else snap.proj_home),
        win_prob=None if snap is None else (snap.home_win_prob if home else 1 - snap.home_win_prob),
        spread=None if snap is None else sign * snap.spread,
        adjusted=snap is not None and snap.adjusted,
        opponent_rating=diff.opponent_rating if diff else None,
        opponent_rank=diff.opponent_rank if diff else None,
        benchmark_win_prob=diff.benchmark_win_prob if diff else None,
        in_resume=diff.in_resume if diff else False,
    )
