from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from tsi.ingest.cache import DiskCache
from tsi.ingest.client import BudgetExceededError, CfbdClient, CfbdError

API_KEY = "fakekey"  # deliberately low-entropy so the gitleaks hook doesn't flag it
GAMES = [{"id": 1}, {"id": 2}]


class FakeApi:
    """Records requests and answers with a fixed status/body."""

    def __init__(self, status: int = 200, body: object = GAMES) -> None:
        self.status = status
        self.body = body
        self.requests: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(self.status, json=self.body)


class Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def make_client(
    tmp_path: Path, ledger, api: FakeApi, budget: int = 1000, clock: Clock | None = None
) -> CfbdClient:
    http = httpx.Client(base_url="https://cfbd.test", transport=httpx.MockTransport(api.handler))
    return CfbdClient(
        api_key=SecretStr(API_KEY),
        cache=DiskCache(tmp_path),
        ledger=ledger,
        monthly_budget=budget,
        http=http,
        **({"clock": clock} if clock else {}),
    )


def test_first_call_fetches_with_bearer_then_cache_serves(tmp_path: Path, ledger) -> None:
    api = FakeApi()
    client = make_client(tmp_path, ledger, api)

    assert client.get("/games", {"year": 2024}) == GAMES
    assert client.get("/games", {"year": 2024}) == GAMES

    assert len(api.requests) == 1
    assert api.requests[0].headers["Authorization"] == f"Bearer {API_KEY}"
    assert api.requests[0].url.params["year"] == "2024"
    assert [r.from_cache for r in ledger.records] == [False, True]
    assert ledger.records[0].row_count == 2


def test_refresh_bypasses_cache(tmp_path: Path, ledger) -> None:
    api = FakeApi()
    client = make_client(tmp_path, ledger, api)

    client.get("/games", {"year": 2024})
    client.get("/games", {"year": 2024}, refresh=True)

    assert len(api.requests) == 2


def test_live_season_cache_expires_and_refetches(tmp_path: Path, ledger) -> None:
    api = FakeApi()
    clock = Clock(datetime(2026, 10, 14, 10, 0, tzinfo=UTC))
    client = make_client(tmp_path, ledger, api, clock=clock)

    client.get("/games", {"year": 2026})
    clock.now += timedelta(hours=1)
    client.get("/games", {"year": 2026})  # same day: cache
    clock.now += timedelta(days=1)
    client.get("/games", {"year": 2026})  # next day: fresh fetch

    assert len(api.requests) == 2
    assert [r.from_cache for r in ledger.records] == [False, True, False]


def test_get_response_reports_original_fetch_time(tmp_path: Path, ledger) -> None:
    clock = Clock(datetime(2026, 10, 14, 10, 0, tzinfo=UTC))
    client = make_client(tmp_path, ledger, FakeApi(), clock=clock)

    first = client.get_response("/games", {"year": 2026})
    clock.now += timedelta(hours=1)
    second = client.get_response("/games", {"year": 2026})  # cached

    assert first.fetched_at == second.fetched_at == datetime(2026, 10, 14, 10, 0, tzinfo=UTC)


def test_none_params_are_dropped(tmp_path: Path, ledger) -> None:
    api = FakeApi()
    make_client(tmp_path, ledger, api).get("/games", {"year": 2024, "week": None})

    assert "week" not in api.requests[0].url.params


def test_budget_blocks_requests_but_not_cache_hits(tmp_path: Path, ledger) -> None:
    api = FakeApi()
    client = make_client(tmp_path, ledger, api, budget=1)
    client.get("/games", {"year": 2024})  # uses the only call

    with pytest.raises(BudgetExceededError, match="1/1"):
        client.get("/games", {"year": 2023})
    assert client.get("/games", {"year": 2024}) == GAMES  # cached: still fine
    assert len(api.requests) == 1


def test_http_error_is_recorded_and_never_leaks_key(tmp_path: Path, ledger) -> None:
    api = FakeApi(status=401, body={"error": "unauthorized"})
    client = make_client(tmp_path, ledger, api)

    with pytest.raises(CfbdError) as exc_info:
        client.get("/games", {"year": 2024})

    assert "HTTP 401" in str(exc_info.value)
    assert API_KEY not in str(exc_info.value)
    assert ledger.records[-1].status == "error"
    assert ledger.records[-1].from_cache is False
    assert DiskCache(tmp_path).get("/games", {"year": 2024}) is None  # errors aren't cached


def test_cache_files_never_contain_the_key(tmp_path: Path, ledger) -> None:
    make_client(tmp_path, ledger, FakeApi()).get("/games", {"year": 2024})

    for path in tmp_path.rglob("*.json"):
        assert API_KEY not in path.read_text(encoding="utf-8")
