from tsi.ingest.transform.venues import venue_row, venue_rows


def test_venue_row_parses_elevation_meters(cfbd_fixture) -> None:
    raw = next(v for v in cfbd_fixture("venues_sample") if v["name"] == "Folsom Field")

    row = venue_row(raw)

    assert row == {
        "id": 3726,
        "name": "Folsom Field",
        "city": "Boulder",
        "state": "CO",
        "latitude": 40.0094746,
        "longitude": -105.266905,
        "elevation_m": 1634.041138,
        "dome": False,
    }


def test_placeholder_without_id_is_dropped() -> None:
    assert venue_row({"id": None, "name": None}) is None


def test_missing_elevation_is_none() -> None:
    assert venue_row({"id": 1, "name": "X", "elevation": None})["elevation_m"] is None


def test_venue_rows_deduplicate_by_id() -> None:
    rows = venue_rows([{"id": 1, "name": "Old"}, {"id": 1, "name": "New"}, {"id": None}])

    assert [(r["id"], r["name"]) for r in rows] == [(1, "New")]
