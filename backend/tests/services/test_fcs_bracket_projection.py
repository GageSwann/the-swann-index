"""The official FCS bracket's checks and known games (#157)."""

from datetime import UTC, datetime

import pytest

from tsi.db.queries.playoff_games import BracketMismatchError, PlayoffGame
from tsi.services.fcs_bracket_projection import check_first_round, known_games
from tsi.sim.fcs_format import FCS_FORMAT_2026 as FMT

FIELD = list(range(100, 124))  # team ids by position
KICK = datetime(2026, 11, 28, 18, tzinfo=UTC)


def game(gid, home, away, hp=None, ap=None, notes="FCS Championship - First Round", neutral=False):
    done = hp is not None
    return PlayoffGame(gid, KICK, home, away, neutral, hp, ap, done, notes)


def first_round() -> list[PlayoffGame]:
    return [game(i, FIELD[hi - 1], FIELD[lo - 1]) for i, (hi, lo) in enumerate(FMT.first_round)]


def test_the_entered_first_round_must_match_cfbd() -> None:
    check_first_round(FIELD, first_round(), FMT)  # hosts may be either way round
    swapped = first_round()
    swapped[0] = game(0, FIELD[23], FIELD[8])
    check_first_round(FIELD, swapped, FMT)

    wrong = first_round()
    wrong[0] = game(0, FIELD[8], FIELD[22])  # 9 v 23 isn't in the bracket
    with pytest.raises(BracketMismatchError):
        check_first_round(FIELD, wrong, FMT)
    with pytest.raises(BracketMismatchError):
        check_first_round(FIELD, [], FMT)  # not announced yet


def test_known_games_in_simulation_indexes() -> None:
    index = {t: i + 50 for i, t in enumerate(FIELD)}
    games = [
        game(1, 115, 116, 20, 27),  # the visitor won
        game(2, 108, 123),  # scheduled
        game(3, 100, 101, notes="FCS Championship - Final", neutral=True),
        game(4, 999, 100),  # a team outside the simulation: skipped
    ]

    known = known_games(games, index)

    assert known.winners == {(65, 66): 66}
    assert known.sites == {(65, 66): (65, False), (58, 73): (58, False), (50, 51): (50, True)}
