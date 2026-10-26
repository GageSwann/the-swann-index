"""Every v1 endpoint against a seeded throwaway schema (tests/db_integration/api_seed.py)."""

import pytest
from fastapi.testclient import TestClient
from tests.db_integration.api_seed import NOW, WEEK1_RUN_AT, WEEK2_RUN_AT, seed

from tsi.api.app import create_app
from tsi.api.deps import get_now, get_session
from tsi.config import Settings


@pytest.fixture
def api(sessions) -> TestClient:
    with sessions.begin() as s:
        seed(s)
    settings = Settings(cfbd_api_key="fakekey", database_url="postgresql+psycopg://u:fakekey@x/y")
    app = create_app(settings)

    def session_override():
        with sessions() as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[get_now] = lambda: NOW
    with TestClient(app) as client:
        yield client


def ok(api: TestClient, path: str) -> dict:
    r = api.get(path)
    assert r.status_code == 200, (path, r.text)
    return r.json()


def test_meta(api: TestClient) -> None:
    meta = ok(api, "/meta/current")

    assert (meta["season"], meta["season_type"], meta["week"]) == (2026, "regular", 2)
    assert meta["ratings_updated_at"].startswith(WEEK2_RUN_AT.isoformat()[:16])
    assert meta["predictions_published_at"] is not None


def test_power_and_resume_rankings(api: TestClient) -> None:
    power = ok(api, "/rankings")
    resume = ok(api, "/rankings?type=resume")

    assert [t["team"]["school"] for t in power["teams"]] == ["Alpha", "Delta", "Charlie", "Bravo"]
    assert [t["team"]["school"] for t in resume["teams"]] == ["Alpha", "Delta", "Bravo", "Charlie"]
    alpha = power["teams"][0]
    assert (alpha["wins"], alpha["losses"], alpha["rating"]) == (1, 0, 12.0)
    assert alpha["predictive_rating"] == 14.0 and alpha["team"]["conference"] == "Test"
    assert alpha["sos"] == 1.5
    assert alpha["previous_rank"] == 1  # same rank a week earlier (the week-1 run)
    assert (alpha["off_rank"], alpha["def_rank"]) == (1, 1)  # off 7.0, def 5.0: both best
    assert power["as_of"].startswith(WEEK2_RUN_AT.isoformat()[:16])
    assert power["previous_as_of"].startswith(WEEK1_RUN_AT.isoformat()[:16])  # 7 days earlier


def test_rankings_for_an_earlier_week_and_missing_season(api: TestClient) -> None:
    week1 = ok(api, "/rankings?week=1")

    assert week1["as_of"].startswith(WEEK1_RUN_AT.isoformat()[:16])
    assert week1["teams"][0]["rating"] == 11.0
    assert api.get("/rankings?season=2015").status_code == 404


def test_team_list_and_profile(api: TestClient) -> None:
    teams = ok(api, "/teams")
    alpha = ok(api, "/teams/alpha")

    assert [t["school"] for t in teams] == ["Alpha", "Bravo", "Charlie", "Delta"]  # FBS only
    assert (alpha["wins"], alpha["losses"], alpha["ratings"]["rank_power"]) == (1, 0, 1)
    assert len(alpha["history"]) == 2
    first, live = alpha["schedule"]
    assert (first["outcome"], first["team_points"], first["opponent"]["slug"]) == ("W", 30, "bravo")
    # In progress: the locked pre-kickoff snapshot (Alpha -4), never the post-kickoff one (-9).
    assert live["spread"] == -4.0 and live["site"] == "home"
    assert api.get("/teams/nope").status_code == 404


def test_week_board(api: TestClient) -> None:
    board = ok(api, "/weeks/2026/2/games")
    games = {g["id"]: g for g in board["games"]}

    assert set(games) == {201, 202}  # the FCS-only game is left out
    live = games[201]["prediction"]
    assert live["locked"] is True and live["spread"] == -4.0 and live["picks"] == []
    upcoming = games[202]
    assert upcoming["prediction"]["locked"] is False
    assert [p["side"] for p in upcoming["prediction"]["picks"]] == ["over"]
    market = upcoming["market"]
    assert (market["spread"], market["total"], market["books"]) == (-3.25, 50.5, 2)  # median


def test_game_center(api: TestClient) -> None:
    center = ok(api, "/games/202")

    assert center["game"]["home"]["school"] == "Bravo"
    assert center["markets"]["spread"]["line"] == -5.0  # re-priced from the stored distribution
    assert center["markets"]["total"]["line"] == 57.0
    assert len(center["markets"]["alt_spreads"]) == 21
    assert len(center["history"]) == 1
    assert ok(api, "/games/101")["game"]["result"] == {
        "home_points": 30,
        "away_points": 20,
        "final": True,
    }
    assert api.get("/games/999").status_code == 404


def test_ledger(api: TestClient) -> None:
    ledger = ok(api, "/book/ledger")

    statuses = {p["game_id"]: p["status"] for p in ledger["picks"]}
    assert statuses == {101: "graded", 202: "open"}  # the post-kickoff pick on 201 never counts
    overall = next(r for r in ledger["records"] if r["market"] == "all")
    assert (overall["wins"], overall["losses"]) == (1, 0)
    assert overall["units"] == pytest.approx(100 / 110)
    assert overall["clv"] == pytest.approx(1.5)
    assert len(ledger["cumulative"]) == 1


def test_model_report(api: TestClient) -> None:
    report = ok(api, "/model/report")

    assert report["backtest"]["metrics"]["validate_mae"] == 12.4
    tables = report["backtest"]["report"]
    assert tables["by_season"][0]["label"] == "2024"
    assert tables["periods"][0]["predictive_mae"] == 12.4
    assert tables["book"][0]["wins"] == 104
    assert tables["book_units"][0]["date"] == "2023-09-02"
    assert [v["model_version"] for v in report["versions"]] == ["tsi-old", "tsi-test"]
    assert report["versions"][0]["validate_mae"] == 12.9
    live = report["live"]
    assert live["games"] == 1  # game 101: finished with a locked snapshot
    assert live["mae"] == pytest.approx(abs(6.0 - 10))
    assert live["market_mae"] == pytest.approx(abs(7.0 - 10))


def test_matchup(api: TestClient) -> None:
    m = ok(api, "/matchup?home=alpha&away=delta&neutral=true")

    assert m["proj_home"] + m["proj_away"] == pytest.approx(m["total"])
    assert 0 < m["home_win_prob"] < 1 and m["neutral"] is True
    assert api.get("/matchup?home=alpha&away=nope").status_code == 404
    assert api.get("/matchup?home=alpha&away=alpha").status_code == 400
