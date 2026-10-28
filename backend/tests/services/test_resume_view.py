"""The team page's Résumé breakdown: every rated team gets a summary (decision #89)."""

from datetime import UTC, datetime, timedelta

import pytest

from tsi.db.queries.games import GameRow
from tsi.db.queries.team_info import StoredRating, TeamRef
from tsi.model.ratings.probability import win_prob
from tsi.services.read.resume_view import ResumeContext, recomputed_sor, resume_summary

RUN_AT = datetime(2026, 10, 25, 12, tzinfo=UTC)


def ref(tid: int, division: str = "fbs") -> TeamRef:
    return TeamRef(tid, f"t{tid}", f"T{tid}", None, None, None, None, None, None, division)


def rating(tid: int, value: float, sor: float | None = None) -> StoredRating:
    return StoredRating(tid, "season", value, 0.0, 0.0, 5, False, tid, tid, sor, None)


def game(gid: int, home: int, away: int, hp: int | None, ap: int | None, days_ago: int) -> GameRow:
    return GameRow(gid, 2026, 1, "regular", RUN_AT - timedelta(days=days_ago), False, home, away,
                   False, False, hp is not None, hp, ap, None)  # fmt: skip


def context(pooled: dict[str, float] | None) -> ResumeContext:
    season = {1: rating(1, 10.0, sor=0.25), 2: rating(2, 4.0)}
    return ResumeContext(RUN_AT, benchmark=12.0, hfa=3.0, sigma=15.0, season=season, pooled=pooled)


REFS = {1: ref(1), 2: ref(2), 3: ref(3, "fcs")}
GAMES = [
    game(10, 1, 2, 28, 21, days_ago=14),  # home win over FBS team 2
    game(11, 1, 3, 45, 7, days_ago=7),  # home win over an FCS team
    game(12, 2, 1, None, None, days_ago=-7),  # upcoming: never counts
]


def test_summary_is_complete_when_every_opponent_is_rated() -> None:
    res = resume_summary(context({"fcs": -20.0, "lower": -30.0}), GAMES, 1, REFS)

    p_fbs = win_prob(12.0 - 4.0 + 3.0, 15.0)
    p_fcs = win_prob(12.0 + 20.0 + 3.0, 15.0)
    assert res.games == 2 and res.sor == 0.25  # SOR is the stored ranking's value
    assert res.benchmark_expected_wins == pytest.approx(p_fbs + p_fcs)
    # Two wins: SOR = P(the benchmark wins both).
    assert recomputed_sor(context({"fcs": -20.0, "lower": -30.0}), GAMES, 1, REFS) == pytest.approx(
        p_fbs * p_fcs
    )


def test_summary_still_present_without_pooled_ratings() -> None:
    # Runs saved before pooled non-FBS ratings were: the FCS game's difficulty is unknown.
    res = resume_summary(context(None), GAMES, 1, REFS)

    assert res.games == 2 and res.sor == 0.25
    assert res.benchmark_expected_wins is None
    assert recomputed_sor(context(None), GAMES, 1, REFS) is None


def test_summary_before_any_game() -> None:
    res = resume_summary(context(None), [GAMES[2]], 1, REFS)

    assert (res.games, res.benchmark_expected_wins) == (0, 0)
