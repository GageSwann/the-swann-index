"""Pre-kickoff stacking features for one game: margin (model/stack.py) and total (model/totals.py).

Pure functions over already-fitted pieces, shared by the backtest and the live
prediction path so both see exactly the same inputs.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from tsi.model.ratings.components import Components, MetricRatings
from tsi.model.ratings.types import AVERAGE_TEAM, TeamRating, matchup_margin
from tsi.model.totals import scoring_level


@dataclass(frozen=True)
class GameSide:
    """A game's two teams as rated ids (non-FBS opponents mapped to their pool)."""

    home: int
    away: int
    neutral: bool


def margin_features(
    side: GameSide,
    components: Components | None,
    priors: Mapping[int, TeamRating],
    elo_margin: float,
) -> tuple[float, ...]:
    """(site, ppd, success, prior, elo), home view."""
    prior = _get(priors, side.home).rating - _get(priors, side.away).rating
    ppd = _margin(components.ppd, side) if components else 0.0
    success = _margin(components.success, side) if components else 0.0
    return (0.0 if side.neutral else 1.0, ppd, success, prior, elo_margin)


def total_features(
    side: GameSide,
    components: Components | None,
    last: Components | None,  # last season's final components
    priors: Mapping[int, TeamRating],
) -> tuple[float, ...]:
    """(level, ppd, success, pace, tempo, prior, last_pace, last_tempo)."""
    last_level = 2 * last.ppd.level if last else 0.0
    if components is None:
        level = scoring_level(None, last_level, 0)
        now = (0.0, 0.0, 0.0, 0.0)
    else:
        team_games = sum(components.games.values())
        level = scoring_level(2 * components.ppd.level, last_level, team_games)
        now = tuple(
            _sum(m, side)
            for m in (components.ppd, components.success, components.pace, components.tempo)
        )
    home, away = _get(priors, side.home), _get(priors, side.away)
    prior = (home.off - away.defense) + (away.off - home.defense)
    last_pace = _sum(last.pace, side) if last else 0.0
    last_tempo = _sum(last.tempo, side) if last else 0.0
    return (level, *now, prior, last_pace, last_tempo)


def _get(ratings: Mapping[int, TeamRating], team: int) -> TeamRating:
    return ratings.get(team, AVERAGE_TEAM)


def _margin(m: MetricRatings | None, side: GameSide) -> float:
    if m is None:
        return 0.0
    return matchup_margin(_get(m.teams, side.home), _get(m.teams, side.away))


def _sum(m: MetricRatings | None, side: GameSide) -> float:
    """Both offenses vs. the opposing defenses, added: the game-total version of a margin."""
    if m is None:
        return 0.0
    home, away = _get(m.teams, side.home), _get(m.teams, side.away)
    return (home.off - away.defense) + (away.off - home.defense)
