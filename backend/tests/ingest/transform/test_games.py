from datetime import UTC, datetime

import pytest

from tsi.ingest.transform.games import (
    game_rows,
    participant_team_seasons,
    placeholder_teams,
    relevant_games,
)

COLORADO, NDSU = 38, 2449


@pytest.fixture
def raw(cfbd_fixture):
    return cfbd_fixture("games_2024_sample")


def by_id(rows):
    return {r["id"]: r for r in rows}


def test_game_row_maps_fields_and_kickoff_is_utc(raw) -> None:
    game = by_id(game_rows(raw))[401634206]

    assert game["home_id"] == COLORADO and game["away_id"] == NDSU
    assert (game["season"], game["week"], game["season_type"]) == (2024, 1, "regular")
    assert game["start_time"] == datetime(2024, 8, 30, 0, 0, tzinfo=UTC)
    assert (game["home_points"], game["away_points"]) == (31, 26)
    assert game["venue_id"] == 3726
    assert game["completed"] is True
    assert game["start_time_tbd"] is False
    assert game["notes"] is None


def test_unknown_venue_becomes_none(raw) -> None:
    rows = by_id(game_rows(raw, known_venues=set()))

    assert rows[401634206]["venue_id"] is None  # Folsom Field not "known" here
    assert by_id(game_rows(raw, known_venues={3726}))[401634206]["venue_id"] == 3726


def test_tbd_kickoff_is_flagged(raw) -> None:
    assert by_id(game_rows(raw))[401693677]["start_time_tbd"] is True


def test_postseason_keeps_bowl_name(raw) -> None:
    bowl = by_id(game_rows(raw))[401677076]

    assert bowl["season_type"] == "postseason"
    assert bowl["notes"] == "Cricket Celebration Bowl"


def test_incomplete_game_is_kept_with_flag(raw) -> None:
    assert by_id(game_rows(raw))[401640992]["completed"] is False


def test_non_regular_post_games_dropped_and_ids_deduplicated(raw) -> None:
    allstar = dict(raw[0], id=1, seasonType="allstar")
    doubled = raw + [raw[0], allstar]

    ids = [g["id"] for g in relevant_games(doubled)]

    assert sorted(ids) == sorted(g["id"] for g in raw)


def test_placeholders_only_for_unknown_teams(raw) -> None:
    known = {COLORADO, NDSU} | {
        g[f"{s}Id"] for g in raw if g["id"] != 401693677 for s in ("home", "away")
    }

    rows = placeholder_teams(raw, known)

    naia = next(g for g in raw if g["id"] == 401693677)
    assert {r["id"] for r in rows} == {naia["homeId"], naia["awayId"]} - known
    for r in rows:
        assert r["slug"].endswith(f"-{r['id']}")  # can't collide with a real slug


def test_participant_team_seasons_use_game_classification(raw) -> None:
    rows = {r["team_id"]: r for r in participant_team_seasons(raw)}

    assert rows[NDSU] == {"team_id": NDSU, "season": 2024, "conference": "MVFC", "division": "fcs"}
    naia = next(g for g in raw if g["id"] == 401693677)
    unclassified = naia["awayId"] if naia["awayClassification"] is None else naia["homeId"]
    assert rows[unclassified]["division"] == "unknown"
