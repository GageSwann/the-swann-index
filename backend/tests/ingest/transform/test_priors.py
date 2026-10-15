from tsi.ingest.transform.priors import returning_rows, talent_rows

TEAM_IDS = {"Alabama": 333, "Colorado": 38}


def test_talent_rows(cfbd_fixture) -> None:
    rows = {
        r["team_id"]: r for r in talent_rows(cfbd_fixture("talent_2024_sample"), 2024, TEAM_IDS)
    }

    assert rows[333] == {"season": 2024, "team_id": 333, "talent": 1018.28}
    assert rows[38]["talent"] == 749.16


def test_returning_rows_use_percent_ppa(cfbd_fixture) -> None:
    rows = {
        r["team_id"]: r
        for r in returning_rows(cfbd_fixture("returning_2024_sample"), 2024, TEAM_IDS)
    }

    assert rows[38] == {"season": 2024, "team_id": 38, "returning_ppa": 0.665}
    assert "talent" not in rows[38]  # partial row: never overwrites talent


def test_unknown_teams_are_skipped() -> None:
    assert talent_rows([{"team": "Nowhere", "talent": 1.0}], 2024, TEAM_IDS) == []
    assert returning_rows([{"team": "Nowhere", "percentPPA": 0.5}], 2024, TEAM_IDS) == []
