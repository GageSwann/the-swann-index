"""Every v1 endpoint against a seeded throwaway schema (tests/db_integration/api_seed.py)."""

import pytest
from fastapi.testclient import TestClient
from tests.db_integration.api_seed import NOW, WEEK1_RUN_AT, WEEK2_RUN_AT, seed

from tsi.api.app import create_app
from tsi.api.deps import get_now, get_sessions
from tsi.config import Settings
from tsi.model.ratings.probability import win_prob

OWNER_KEY = "fakekey-" + "x" * 32  # low entropy on purpose (gitleaks)
OWNER = {"Authorization": f"Bearer {OWNER_KEY}"}


def make_api(sessions, owner_key: str | None = OWNER_KEY) -> TestClient:
    settings = Settings(
        cfbd_api_key="fakekey",
        database_url="postgresql+psycopg://u:fakekey@x/y",
        owner_api_key=owner_key,
    )
    app = create_app(settings)

    app.dependency_overrides[get_sessions] = lambda: sessions
    app.dependency_overrides[get_now] = lambda: NOW
    return TestClient(app)


@pytest.fixture
def api(sessions) -> TestClient:
    with sessions.begin() as s:
        seed(s)
    with make_api(sessions) as client:
        yield client


def ok(api: TestClient, path: str, headers: dict | None = None) -> dict:
    r = api.get(path, headers=headers)
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

    # FBS only: the seeded FCS teams Echo and Foxtrot have FCS ranks 1 and 2.
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
    assert (alpha["projected_wins"], alpha["conference_title_prob"]) == (3.7, 0.25)  # sim


def test_rankings_for_an_earlier_week_and_missing_season(api: TestClient) -> None:
    week1 = ok(api, "/rankings?week=1")

    assert week1["as_of"].startswith(WEEK1_RUN_AT.isoformat()[:16])
    assert week1["teams"][0]["rating"] == 11.0
    assert week1["teams"][0]["projected_wins"] is None  # that run predates the season sim
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
    assert alpha["adjustments"] == [] and live["adjusted"] is False
    bravo = ok(api, "/teams/bravo")
    assert [a["reason"] for a in bravo["adjustments"]] == ["QB out"]
    assert [g["adjusted"] for g in bravo["schedule"]] == [True, True]  # week 1, Bravo-Delta
    proj = alpha["projection"]
    assert (proj["expected_wins"], proj["win_dist"], proj["win_out_prob"]) == (
        3.7,
        [0.0, 0.25, 0.5, 0.25],
        0.25,
    )
    assert (proj["title_game_prob"], proj["conference_title_prob"]) == (0.5, 0.25)
    assert (proj["playoff_prob"], proj["champion_prob"]) == (0.9, pytest.approx(0.18))
    assert ok(api, "/teams/echo")["projection"]["expected_wins"] == 8.5  # FCS too (#125)


def test_team_resume_breakdown(api: TestClient) -> None:
    alpha = ok(api, "/teams/alpha")
    first, live = alpha["schedule"]
    site = {"home": 1, "away": -1, "neutral": 0}[first["site"]]
    # Bravo's current rating (-8, #4) vs. the benchmark 6.0, home field 3.0, spread 15.0.
    p = win_prob(6.0 - (-8.0) + site * 3.0, 15.0)

    assert (first["opponent_rating"], first["opponent_rank"]) == (-8.0, 4)
    assert first["benchmark_win_prob"] == pytest.approx(p)
    assert first["in_resume"] is True and live["in_resume"] is False  # live: not decided
    res = alpha["resume"]
    assert (res["games"], res["benchmark_rating"], res["benchmark_rank"]) == (1, 6.0, 12)
    assert res["sor"] == 0.20  # the stored ranking's SOR (Alpha's seeded value)
    assert res["benchmark_expected_wins"] == pytest.approx(p)  # one counted game


def test_week_board(api: TestClient) -> None:
    board = ok(api, "/weeks/2026/2/games")
    games = {g["id"]: g for g in board["games"]}

    assert set(games) == {201, 202}  # the FCS-only game is left out
    live = games[201]["prediction"]
    assert live["locked"] is True and live["spread"] == -4.0
    upcoming = games[202]
    assert upcoming["prediction"]["locked"] is False
    # The Book is owner-only (#139): no picks or Book prices in public responses.
    assert not {k for k in upcoming["prediction"] if k == "picks" or k.startswith("book_")}
    assert live["adjusted"] is False and live["raw"] is None and live["adjustments"] == []
    adjusted = upcoming["prediction"]
    assert (adjusted["adjusted"], adjusted["spread"], adjusted["total"]) == (True, -2.0, 54.0)
    assert (adjusted["raw"]["spread"], adjusted["raw"]["total"]) == (-5.0, 57.0)
    (note,) = adjusted["adjustments"]
    assert (note["school"], note["off_points"], note["reason"]) == ("Bravo", -3.0, "QB out")
    market = upcoming["market"]
    assert (market["spread"], market["total"], market["books"]) == (-3.25, 50.5, 2)  # median


def test_game_center(api: TestClient) -> None:
    center = ok(api, "/games/202")

    assert center["game"]["home"]["school"] == "Bravo"
    # Re-priced from the stored (official, adjusted) distribution.
    assert center["markets"]["spread"]["line"] == -2.0
    assert center["markets"]["total"]["line"] == 54.0
    assert len(center["markets"]["alt_spreads"]) == 21
    spread = center["markets"]["spread"]["first"]
    assert set(spread) == {"prob", "fair"}  # TSI's chance and fair odds, no Book price
    assert len(center["history"]) == 1
    assert ok(api, "/games/101")["game"]["result"] == {
        "home_points": 30,
        "away_points": 20,
        "final": True,
    }
    assert api.get("/games/999").status_code == 404


def test_ledger(api: TestClient) -> None:
    ledger = ok(api, "/book/ledger", OWNER)

    statuses = {p["game_id"]: p["status"] for p in ledger["picks"]}
    assert statuses == {101: "graded", 202: "open"}  # the post-kickoff pick on 201 never counts
    overall = next(r for r in ledger["records"] if r["market"] == "all")
    assert (overall["wins"], overall["losses"]) == (1, 0)
    assert overall["units"] == pytest.approx(100 / 110)
    assert overall["clv"] == pytest.approx(1.5)
    assert len(ledger["cumulative"]) == 1


def test_model_report(api: TestClient) -> None:
    report = ok(api, "/model/report", OWNER)

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
    # Raw vs. adjusted on game 101 (Alpha won 30-20): raw -6 / 52, adjusted -8 / 50.
    adj = report["adjustments"]["overall"]
    assert (adj["games"], adj["raw_mae"], adj["adjusted_mae"]) == (1, 4.0, 2.0)
    assert (adj["raw_total_mae"], adj["adjusted_total_mae"]) == (2.0, 0.0)
    assert (adj["raw_su"], adj["adjusted_su"], adj["helped"], adj["hurt"]) == (1.0, 1.0, 1, 0)
    (one,) = report["adjustments"]["adjustments"]
    assert (one["adjustment"]["reason"], one["score"]["games"]) == ("Starting LB back", 1)


def test_matchup(api: TestClient) -> None:
    m = ok(api, "/matchup?home=alpha&away=delta&neutral=true")

    assert m["proj_home"] + m["proj_away"] == pytest.approx(m["total"])
    assert 0 < m["home_win_prob"] < 1 and m["neutral"] is True
    assert m["sigma_margin"] > 0 and m["sigma_total"] > 0  # the margin chart needs them
    assert api.get("/matchup?home=alpha&away=nope").status_code == 404
    assert api.get("/matchup?home=alpha&away=alpha").status_code == 400


def test_playoff_odds_and_projected_bracket(api: TestClient) -> None:
    result = ok(api, "/playoff")

    # Charlie (0%) is left off; the rest by playoff odds.
    assert [t["team"]["school"] for t in result["teams"]] == ["Alpha", "Delta", "Bravo"]
    alpha = result["teams"][0]
    assert (alpha["playoff_prob"], alpha["bye_prob"], alpha["rank_resume"]) == (0.9, 0.45, 1)
    assert alpha["fair_odds"] == {"playoff": -900, "conference": 300, "title": 456}
    assert result["sims"] == 10_000 and "format" not in result  # dropped for `rounds` (#125)
    # Projected field: everyone with a chance, by average seed (Alpha ~1.5, the rest 5).
    assert [t["team"]["school"] for t in result["projected"]][0] == "Alpha"
    assert "Charlie" not in [t["team"]["school"] for t in result["projected"]]
    assert api.get("/playoff?season=2015").status_code == 404
    assert len(result["rounds"]) == 4 and result["rounds"][0]["games"][0] == [
        {"seed": 5, "game": None},
        {"seed": 12, "game": None},
    ]
    assert (result["division"], result["field_size"], result["byes"]) == ("fbs", 12, 4)


def test_fcs_playoff_odds(api: TestClient) -> None:
    result = ok(api, "/playoff?division=fcs")

    assert [t["team"]["school"] for t in result["teams"]] == ["Echo", "Foxtrot"]
    assert (result["division"], result["field_size"], result["byes"]) == ("fcs", 24, 8)
    assert result["seeds"] == 16 and result["rounds"][0]["games"][0][0] == {"seed": 9, "game": None}
    assert [r["name"] for r in result["rounds"]] == [
        "First round", "Second round", "Quarterfinals", "Semifinals", "Championship",
    ]  # fmt: skip
    assert result["rounds"][1]["games"][0] == [{"seed": 1, "game": None}, {"seed": None, "game": 7}]
    assert [t["team"]["school"] for t in result["projected"]] == ["Echo", "Foxtrot"]
    assert api.get("/playoff?division=all").status_code == 422
    echo = ok(api, "/teams/echo")["projection"]
    assert (echo["playoff_prob"], echo["title_game_prob"]) == (0.8, None)


def test_rankings_by_division(api: TestClient) -> None:
    fcs = ok(api, "/rankings?division=fcs")
    both = ok(api, "/rankings?division=all")

    assert (fcs["division"], fcs["benchmark_rank"], both["benchmark_rank"]) == ("fcs", 24, None)
    assert ok(api, "/rankings")["benchmark_rank"] == 12
    assert [(t["rank"], t["team"]["school"]) for t in fcs["teams"]] == [(1, "Echo"), (2, "Foxtrot")]
    # "all": one scale, re-ranked by rating; FCS teams keep their own division ranks too.
    assert [t["team"]["school"] for t in both["teams"]] == [
        "Alpha", "Delta", "Charlie", "Bravo", "Echo", "Foxtrot",
    ]  # fmt: skip
    assert [t["rank"] for t in both["teams"]] == [1, 2, 3, 4, 5, 6]
    assert both["teams"][4]["rank_power"] == 1  # Echo: #1 in FCS
    assert api.get("/rankings?division=all&type=resume").status_code == 422


def test_team_list_and_week_board_by_division(api: TestClient) -> None:
    assert [t["school"] for t in ok(api, "/teams?division=fcs")] == ["Echo", "Foxtrot"]
    assert len(ok(api, "/teams?division=all")) == 6

    def ids(division: str) -> list[int]:
        return [g["id"] for g in ok(api, f"/weeks/2026/2/games?division={division}")["games"]]

    assert (ids("fbs"), ids("fcs"), ids("all")) == ([201, 202], [203], [201, 202, 203])


def test_fcs_team_profile_and_cross_division_matchup(api: TestClient) -> None:
    echo = ok(api, "/teams/echo")

    assert (echo["ratings"]["rating"], echo["ratings"]["rank_power"]) == (-30.0, 1)
    assert len(echo["history"]) == 1  # FCS teams are stored from the week-2 run on
    assert echo["projection"]["conference_title_prob"] == 0.6  # FCS teams are simulated
    # Résumé vs. the #24 FCS team (#114, #133); Echo-Foxtrot is upcoming, so nothing counts.
    resume = echo["resume"]
    assert (resume["benchmark_rating"], resume["benchmark_rank"], resume["games"]) == (
        -25.0, 24, 0,
    )  # fmt: skip
    (foxtrot_game,) = echo["schedule"]
    assert (foxtrot_game["opponent_rating"], foxtrot_game["opponent_rank"]) == (-35.0, 2)
    p = win_prob(-25.0 - (-35.0) + 3.0, 15.0)  # Echo at home, #24 FCS benchmark
    assert foxtrot_game["benchmark_win_prob"] == pytest.approx(p)
    m = ok(api, "/matchup?home=alpha&away=echo")
    assert (m["home"]["division"], m["away"]["division"]) == ("fbs", "fcs")


def test_no_movement_until_the_earlier_run_ranked_the_division(api: TestClient) -> None:
    # The week-1 run predates FCS rankings: FCS and "all" lists show no movement yet.
    for division in ("fcs", "all"):
        board = ok(api, f"/rankings?division={division}")
        assert board["previous_as_of"] is None
        assert all(t["previous_rank"] is None for t in board["teams"])
    assert ok(api, "/rankings")["previous_as_of"] is not None  # FBS keeps its movement


PRIVATE = ("/book/ledger", "/model/report")


@pytest.mark.parametrize("path", PRIVATE)
@pytest.mark.parametrize(
    "headers",
    [
        None,
        {"Authorization": "Bearer wrong-" + "x" * 32},
        {"Authorization": OWNER_KEY},  # no "Bearer"
        {"X-Owner-Key": OWNER_KEY},
    ],
)
def test_private_endpoints_hide_without_the_key(api: TestClient, path: str, headers) -> None:
    r = api.get(path, headers=headers)
    assert (r.status_code, r.json()) == (404, {"detail": "Not Found"})  # same as unknown paths
    assert r.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("path", PRIVATE)
def test_private_endpoints_answer_the_owner_uncached(api: TestClient, path: str) -> None:
    r = api.get(path, headers=OWNER)
    assert r.status_code == 200
    assert r.headers["cache-control"] == "no-store"  # never kept by a shared cache


@pytest.mark.parametrize("path", PRIVATE)
def test_private_endpoints_closed_when_no_key_is_configured(sessions, path: str) -> None:
    with make_api(sessions, owner_key=None) as client:
        assert client.get(path, headers=OWNER).status_code == 404
