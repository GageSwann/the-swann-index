"""Games of the week (Phase 13.4, decision #141): one FBS and one FCS game per ranking.

Picked once per poll week, from the first nightly run on or after Sunday (Eastern), and
held until the next Sunday (#126, #127): the coming games through the next Sunday, between
two teams of the division, scored on

- quality: both teams' ranks in the chosen ranking (Power or Résumé), so a weak team
  pulls the score down;
- closeness: TSI's win probability near 50%;
- stakes: how much a win instead of a loss moves both teams' playoff and conference-title
  odds, read from the season simulation (sim/stakes.py).

The weights are a first guess, not yet tuned on past seasons (roadmap 13.4). Pure: the
nightly run supplies the forecasts, rankings and stakes and stores the picks.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from tsi.divisions import FCS, RATED_DIVISION
from tsi.services.compute_rankings import Rankings, TeamRanking
from tsi.services.predict import GameForecast
from tsi.sim.stakes import GameStakes, stakes_value

EASTERN = ZoneInfo("America/New_York")
WEIGHTS = {"quality": 0.5, "closeness": 0.25, "stakes": 0.25}  # untuned (#141)
RANKED = 25
DIVISIONS = (RATED_DIVISION, FCS)
RANKING_TYPES = ("power", "resume")


@dataclass(frozen=True)
class GameOfWeekPick:
    division: str  # fbs / fcs
    ranking_type: str  # power / resume
    game_id: int
    score: float
    quality: float  # 0..1
    closeness: float  # 0..1
    stakes: float  # 0..1
    home_rank: int | None  # in the chosen ranking, within the division
    away_rank: int | None
    home_playoff_swing: float | None  # P(field | win) - P(field | loss)
    away_playoff_swing: float | None
    home_title_swing: float | None  # the same for the conference title
    away_title_swing: float | None


def poll_sunday(now: datetime) -> date:
    """The poll week a moment belongs to: the most recent Sunday (Eastern) on or before it."""
    day = now.astimezone(EASTERN).date()
    return day - timedelta(days=(day.weekday() + 1) % 7)  # Sun 0, Mon 1 ... Sat 6


def window_end(poll: date) -> datetime:
    """Games of the week come from games before the end of the next Sunday (Eastern)."""
    monday = poll + timedelta(days=8)
    return datetime.combine(monday, time(0), tzinfo=EASTERN).astimezone(UTC)


def pick_games_of_week(
    forecasts: Sequence[GameForecast],
    rankings: Rankings,
    stakes: dict[int, GameStakes],
    now: datetime,
) -> list[GameOfWeekPick]:
    """The best game per division and ranking among games kicking off in (now, window end]."""
    end = window_end(poll_sunday(now))
    picks = []
    for division in DIVISIONS:
        rows = rankings.teams if division == RATED_DIVISION else rankings.fcs_teams
        candidates = [
            f
            for f in forecasts
            if now < f.game.start_time < end
            and f.game.home_div == division
            and f.game.away_div == division
        ]
        for kind in RANKING_TYPES:
            ranks = _ranks(rows, kind)
            scored = [_score(f, division, kind, ranks, stakes.get(f.game.id)) for f in candidates]
            if scored:
                picks.append(max(scored, key=lambda p: (p.score, -p.game_id)))
    return picks


def _ranks(rows: Sequence[TeamRanking], kind: str) -> dict[int, int]:
    return {r.team_id: (r.rank_power if kind == "power" else r.rank_resume) for r in rows}


def _score(
    f: GameForecast,
    division: str,
    kind: str,
    ranks: dict[int, int],
    stakes: GameStakes | None,
) -> GameOfWeekPick:
    g = f.game
    home_rank, away_rank = ranks.get(g.home_id), ranks.get(g.away_id)
    quality = (_rank_value(home_rank) + _rank_value(away_rank)) / 2
    p = f.distribution.home_win_prob
    closeness = 1 - abs(2 * p - 1)
    worth = 0.0 if stakes is None else (stakes_value(stakes.home) + stakes_value(stakes.away)) / 2
    score = (
        WEIGHTS["quality"] * quality + WEIGHTS["closeness"] * closeness + WEIGHTS["stakes"] * worth
    )
    return GameOfWeekPick(
        division=division,
        ranking_type=kind,
        game_id=g.id,
        score=score,
        quality=quality,
        closeness=closeness,
        stakes=worth,
        home_rank=home_rank,
        away_rank=away_rank,
        home_playoff_swing=stakes.home.playoff if stakes else None,
        away_playoff_swing=stakes.away.playoff if stakes else None,
        home_title_swing=stakes.home.title if stakes else None,
        away_title_swing=stakes.away.title if stakes else None,
    )


def _rank_value(rank: int | None) -> float:
    """#1 -> 1, #25 -> 0.04, outside the Top 25 -> 0."""
    return 0.0 if rank is None else max(0, RANKED + 1 - rank) / RANKED
