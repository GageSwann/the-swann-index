import pytest

from tsi.ingest.transform.teams import (
    slugify,
    team_rows,
    team_season_rows,
    team_venues,
)


@pytest.mark.parametrize(
    ("school", "slug"),
    [
        ("Texas A&M", "texas-am"),
        ("Hawai'i", "hawaii"),
        ("Miami (OH)", "miami-oh"),
        ("San José State", "san-jose-state"),
        ("UT San Antonio", "ut-san-antonio"),
        ("St. Francis (PA)", "st-francis-pa"),
    ],
)
def test_slugify(school: str, slug: str) -> None:
    assert slugify(school) == slug


@pytest.fixture
def raw(cfbd_fixture):
    return cfbd_fixture("teams_2024_sample")


def test_team_rows_map_identity_fields(raw) -> None:
    rows = {r["school"]: r for r in team_rows(raw)}
    colorado = rows["Colorado"]

    assert colorado["id"] == 38
    assert colorado["slug"] == "colorado"
    assert colorado["color"] == "#cfb87c"
    assert colorado["alt_color"] == "#000000"
    assert colorado["logo_url"].endswith("/logos/500/38.png")
    assert colorado["venue_id"] == 3726
    assert "conference" not in colorado and "division" not in colorado


def test_team_without_location_has_no_venue(raw) -> None:
    rows = {r["school"]: r for r in team_rows(raw)}

    assert rows["Cheyney"]["venue_id"] is None


def test_slug_collisions_get_id_suffix() -> None:
    raw = [{"id": 2, "school": "Miami"}, {"id": 1, "school": "Miami"}]

    slugs = {r["id"]: r["slug"] for r in team_rows(raw)}

    assert slugs == {1: "miami", 2: "miami-2"}


def test_team_season_rows_use_classification_as_division(raw) -> None:
    rows = {r["team_id"]: r for r in team_season_rows(raw, 2024)}

    assert rows[38] == {
        "team_id": 38,
        "season": 2024,
        "conference": "Big 12",
        "division": "fbs",
        "conference_division": None,
    }
    ndsu = next(t["id"] for t in raw if t["school"] == "North Dakota State")
    assert rows[ndsu]["division"] == "fcs"


def test_team_season_rows_keep_the_conference_division() -> None:
    raw = [{"id": 1, "conference": "Sun Belt", "division": "East", "classification": "fbs"}]

    assert team_season_rows(raw, 2026)[0]["conference_division"] == "East"


def test_team_venues_returns_embedded_locations(raw) -> None:
    venues = team_venues(raw)

    assert len(venues) == len(raw)  # includes the empty placeholder; venue_rows drops it
