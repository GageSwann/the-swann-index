from datetime import UTC, datetime

from tsi.ingest.transform.calendar import calendar_rows


def test_calendar_rows_from_real_sample(cfbd_fixture) -> None:
    rows = calendar_rows(cfbd_fixture("calendar_2024_sample"))

    assert rows[0] == {
        "season": 2024,
        "season_type": "regular",
        "week": 1,
        "start_date": rows[0]["start_date"],
        "end_date": rows[0]["end_date"],
    }
    assert rows[0]["start_date"].tzinfo is UTC
    post = rows[-1]
    assert (post["season_type"], post["week"]) == ("postseason", 1)
    assert post["end_date"] == datetime(2025, 1, 22, 7, 59, tzinfo=UTC)


def test_other_season_types_are_dropped() -> None:
    raw = [
        {
            "season": 2024,
            "seasonType": "allstar",
            "week": 1,
            "startDate": "2025-01-25T08:00:00.000Z",
            "endDate": "2025-02-01T07:59:00.000Z",
        }
    ]

    assert calendar_rows(raw) == []
