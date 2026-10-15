import copy

import pytest

from tsi.ingest.transform.stats import team_game_stat_rows

GAME, COLORADO, NDSU = 401634206, 38, 2449
INDEX = {GAME: {"Colorado": (COLORADO, 31), "North Dakota State": (NDSU, 26)}}


@pytest.fixture
def filtered(cfbd_fixture):
    return cfbd_fixture("advanced_2024_filtered_sample")


@pytest.fixture
def full(cfbd_fixture):
    return cfbd_fixture("advanced_2024_full_sample")


def by_team(rows):
    return {r["team_id"]: r for r in rows}


def test_maps_offense_efficiency_and_points(filtered, full) -> None:
    colorado = by_team(team_game_stat_rows(filtered, full, INDEX))[COLORADO]

    assert colorado["game_id"] == GAME
    assert colorado["points"] == 31
    assert colorado["epa_per_play"] == pytest.approx(0.348834, abs=1e-6)
    assert colorado["success_rate"] == pytest.approx(0.543860, abs=1e-6)
    assert colorado["explosiveness"] == pytest.approx(1.359427, abs=1e-6)
    assert colorado["rush_epa_per_play"] == pytest.approx(-0.170799, abs=1e-6)
    assert colorado["pass_epa_per_play"] == pytest.approx(0.675461, abs=1e-6)
    assert colorado["garbage_time_filtered"] is True


def test_plays_and_drives_come_from_full_game(filtered, full) -> None:
    full = copy.deepcopy(full)
    for row in full:
        row["offense"]["drives"] += 2  # garbage-time drives exist only in the full version
        row["offense"]["plays"] += 10
        row["offense"]["ppa"] = 99.0  # full-game efficiency must NOT be used

    colorado = by_team(team_game_stat_rows(filtered, full, INDEX))[COLORADO]

    assert (colorado["drives"], colorado["plays"]) == (11, 67)
    assert colorado["epa_per_play"] == pytest.approx(0.348834, abs=1e-6)


def test_one_row_per_team_per_game(filtered, full) -> None:
    rows = team_game_stat_rows(filtered + filtered, full, INDEX)

    assert sorted((r["game_id"], r["team_id"]) for r in rows) == [(GAME, COLORADO), (GAME, NDSU)]


def test_unknown_game_or_school_is_skipped(filtered, full) -> None:
    assert team_game_stat_rows(filtered, full, {}) == []
    renamed = [dict(r, team="Somewhere Else") for r in filtered]
    assert team_game_stat_rows(renamed, full, INDEX) == []


def test_missing_full_row_leaves_volume_empty(filtered) -> None:
    colorado = by_team(team_game_stat_rows(filtered, [], INDEX))[COLORADO]

    assert colorado["plays"] is None and colorado["drives"] is None
    assert colorado["epa_per_play"] is not None
