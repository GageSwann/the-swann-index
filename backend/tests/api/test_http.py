"""CORS, caching headers, ETag/304 and gzip, without a database (no route here touches it)."""

import pytest
from fastapi.testclient import TestClient

from tsi.api.app import create_app
from tsi.api.caching import DEFAULT_POLICY, NO_STORE, cache_policy
from tsi.config import Settings

WEB = "https://tsi.example"


@pytest.fixture
def client() -> TestClient:
    settings = Settings(
        cfbd_api_key="fakekey",
        database_url="postgresql+psycopg://user:fakekey@localhost:5432/none",
        tsi_cors_origins=[WEB],
    )
    with TestClient(create_app(settings)) as c:  # the engine connects lazily: never here
        yield c


def test_cache_policy_by_path_and_status() -> None:
    assert cache_policy("/rankings", 200) == DEFAULT_POLICY
    assert cache_policy("/matchup", 200) == "public, max-age=3600"
    assert cache_policy("/teams/nope", 404) == NO_STORE
    assert cache_policy("/matchupx", 200) == DEFAULT_POLICY  # prefix match is per path segment


def test_json_gets_cache_control_and_etag_then_304(client: TestClient) -> None:
    first = client.get("/openapi.json")
    assert first.status_code == 200
    assert first.headers["cache-control"] == DEFAULT_POLICY
    tag = first.headers["etag"]

    again = client.get("/openapi.json", headers={"If-None-Match": tag})
    assert again.status_code == 304 and again.content == b""
    assert again.headers["etag"] == tag

    changed = client.get("/openapi.json", headers={"If-None-Match": '"stale"'})
    assert changed.status_code == 200


def test_cors_allows_only_the_web_origin(client: TestClient) -> None:
    ok = client.options(
        "/rankings", headers={"Origin": WEB, "Access-Control-Request-Method": "GET"}
    )
    assert ok.headers["access-control-allow-origin"] == WEB

    other = client.get("/openapi.json", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in other.headers

    simple = client.get("/openapi.json", headers={"Origin": WEB})
    assert simple.headers["access-control-allow-origin"] == WEB
    assert "etag" in simple.headers["access-control-expose-headers"].lower()


def test_large_responses_are_gzipped(client: TestClient) -> None:
    r = client.get("/openapi.json", headers={"Accept-Encoding": "gzip"})

    assert r.headers.get("content-encoding") == "gzip"
