"""Turn a season's conference membership and games into the sim's `Conference` inputs.

Standings games: conference games between two members, finished (result) or still to
play (a column of the simulated margins). A game billed as a championship between two
members is the title game: once scheduled it decides the champion. Divisions come
from `team_seasons.conference_division` (only the Sun Belt has them in 2026).
"""

from collections import defaultdict
from collections.abc import Callable, Sequence
from datetime import datetime

import numpy as np

from tsi.db.queries.conference import ConferenceGameRow, Member
from tsi.sim.conference import Conference
from tsi.sim.standings import ConferenceGame

NO_TITLE_GAME = frozenset({"FBS Independents"})

NeutralMargin = Callable[[int, int], float]  # (team a, team b) -> a's mean margin, neutral site


def build_conferences(
    members: Sequence[Member],
    games: Sequence[ConferenceGameRow],
    index: dict[int, int],  # team id -> simulation team index
    column_of: dict[int, int],  # remaining game id -> simulated column
    neutral: NeutralMargin,
    now: datetime,
) -> list[Conference]:
    by_conf: dict[str, list[Member]] = defaultdict(list)
    for m in members:
        if m.conference and m.conference not in NO_TITLE_GAME:
            by_conf[m.conference].append(m)
    return [
        _conference(
            name,
            sorted(by_conf[name], key=lambda m: m.team_id),
            games,
            index,
            column_of,
            neutral,
            now,
        )
        for name in sorted(by_conf)
    ]


def _conference(
    name: str,
    members: list[Member],
    games: Sequence[ConferenceGameRow],
    index: dict[int, int],
    column_of: dict[int, int],
    neutral: NeutralMargin,
    now: datetime,
) -> Conference:
    ids = [m.team_id for m in members]
    local = {t: i for i, t in enumerate(ids)}
    standings: list[ConferenceGame] = []
    title = None
    for g in games:
        if g.home_id not in local or g.away_id not in local:
            continue
        game = _game(g, local, column_of, now)
        if game is None:
            continue
        if g.title_game:
            title = game
        elif g.conference_game:
            standings.append(game)
    return Conference(
        name=name,
        teams=tuple(index[t] for t in ids),
        games=tuple(standings),
        neutral_margin=_margins(ids, neutral),
        divisions=_divisions(members),
        title_game=title,
    )


def _game(
    g: ConferenceGameRow, local: dict[int, int], column_of: dict[int, int], now: datetime
) -> ConferenceGame | None:
    home, away = local[g.home_id], local[g.away_id]
    if g.id in column_of:
        return ConferenceGame(home, away, column=column_of[g.id])
    played = g.completed and g.home_points is not None and g.away_points is not None
    if (
        played
        and g.start_time is not None
        and g.start_time < now
        and g.home_points != g.away_points
    ):
        return ConferenceGame(home, away, home_won=g.home_points > g.away_points)
    return None  # not played (postponed, cancelled) or a tie: doesn't count


def _margins(ids: list[int], neutral: NeutralMargin) -> np.ndarray:
    k = len(ids)
    m = np.zeros((k, k))
    for i in range(k):
        for j in range(i + 1, k):
            m[i, j] = neutral(ids[i], ids[j])
            m[j, i] = -m[i, j]
    return m


def _divisions(members: list[Member]) -> tuple[tuple[int, ...], ...] | None:
    groups: dict[str, list[int]] = defaultdict(list)
    for i, m in enumerate(members):
        if m.conference_division:
            groups[m.conference_division].append(i)
    if len(groups) < 2 or sum(map(len, groups.values())) != len(members):
        return None  # no divisions (or incomplete data): top two meet
    return tuple(tuple(groups[d]) for d in sorted(groups))
