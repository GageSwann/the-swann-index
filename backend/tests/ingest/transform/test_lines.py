from datetime import UTC, datetime, timedelta

import pytest

from tsi.ingest.transform.lines import (
    VALUE_FIELDS,
    StoredLine,
    line_snapshots,
    plan_line_changes,
)

COLORADO_GAME, ARIZONA_GAME = 401634206, 401636940
KICKOFF = datetime(2024, 8, 30, tzinfo=UTC)


@pytest.fixture
def snapshots(cfbd_fixture):
    return line_snapshots(cfbd_fixture("lines_2024_sample"))


def values(snap):
    return tuple(snap[f] for f in VALUE_FIELDS)


def test_home_favorite_has_negative_spread(snapshots) -> None:
    dk = snapshots[(COLORADO_GAME, "DraftKings")]  # "Colorado -9", Colorado is home

    assert dk["spread"] == -9.0
    assert dk["spread_open"] == -8.0
    assert dk["total"] == 59.0
    assert (dk["home_ml"], dk["away_ml"]) == (-470, 360)


def test_away_favorite_has_positive_spread(snapshots) -> None:
    # Arizona (home) vs Arizona State: "Arizona State -7.5"; ASU moneyline is negative.
    line = snapshots[(ARIZONA_GAME, "Bovada")]

    assert line["spread"] == 7.5
    assert line["away_ml"] < 0 < line["home_ml"]


def test_missing_numbers_stay_none_and_empty_games_skipped(snapshots) -> None:
    espn = snapshots[(COLORADO_GAME, "ESPN Bet")]

    assert espn["spread_open"] is None and espn["home_ml"] is None
    assert {key[0] for key in snapshots} == {COLORADO_GAME, ARIZONA_GAME}  # App State-Liberty: none


def test_first_snapshot_after_kickoff_is_closing(snapshots) -> None:
    plan = plan_line_changes(snapshots, {}, {COLORADO_GAME: KICKOFF}, KICKOFF + timedelta(days=700))

    assert len(plan.inserts) == 3  # Colorado game only; Arizona game isn't in `kickoff`
    assert plan.skipped == 3
    assert all(row["is_closing"] for row in plan.inserts)


def test_unchanged_pre_kickoff_snapshot_adds_nothing(snapshots) -> None:
    key = (COLORADO_GAME, "DraftKings")
    latest = {key: StoredLine(1, values(snapshots[key]), is_closing=False)}

    plan = plan_line_changes(
        {key: snapshots[key]}, latest, {COLORADO_GAME: KICKOFF}, KICKOFF - timedelta(days=1)
    )

    assert plan.inserts == [] and plan.mark_closing == []
    assert plan.unchanged == 1


def test_line_move_adds_a_new_pre_kickoff_snapshot(snapshots) -> None:
    key = (COLORADO_GAME, "DraftKings")
    moved = dict(snapshots[key], spread=-10.0)
    latest = {key: StoredLine(1, values(snapshots[key]), is_closing=False)}

    plan = plan_line_changes(
        {key: moved}, latest, {COLORADO_GAME: KICKOFF}, KICKOFF - timedelta(hours=3)
    )

    assert [(r["spread"], r["is_closing"]) for r in plan.inserts] == [(-10.0, False)]


def test_unchanged_after_kickoff_marks_existing_row_closing(snapshots) -> None:
    key = (COLORADO_GAME, "DraftKings")
    latest = {key: StoredLine(7, values(snapshots[key]), is_closing=False)}

    plan = plan_line_changes(
        {key: snapshots[key]}, latest, {COLORADO_GAME: KICKOFF}, KICKOFF + timedelta(hours=8)
    )

    assert plan.inserts == []
    assert plan.mark_closing == [7]


def test_already_closing_is_left_alone(snapshots) -> None:
    key = (COLORADO_GAME, "DraftKings")
    latest = {key: StoredLine(7, values(snapshots[key]), is_closing=True)}

    plan = plan_line_changes(
        {key: snapshots[key]}, latest, {COLORADO_GAME: KICKOFF}, KICKOFF + timedelta(days=2)
    )

    assert plan.inserts == [] and plan.mark_closing == []


def test_unknown_kickoff_is_never_closing(snapshots) -> None:
    plan = plan_line_changes(snapshots, {}, {COLORADO_GAME: None}, KICKOFF + timedelta(days=9))

    assert not any(row["is_closing"] for row in plan.inserts)
