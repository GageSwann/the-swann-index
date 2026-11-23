"""Reading the period's transfer from Neon's project details (faked HTTP, no real calls)."""

from datetime import UTC, datetime

import httpx
import pytest
from pydantic import SecretStr

from tsi.ops.neon_api import NeonApiError, fetch_project_usage

KEY = "fakekey"


def client(status: int, body: object, seen: list[httpx.Request] | None = None) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return httpx.Response(status, json=body)

    return httpx.Client(base_url="https://neon.test", transport=httpx.MockTransport(handler))


def test_reads_transfer_and_period() -> None:
    seen: list[httpx.Request] = []
    body = {
        "project": {
            "id": "p1",
            "data_transfer_bytes": 480_000_000,
            "consumption_period_start": "2026-11-20T00:00:00Z",
            "consumption_period_end": "2026-12-01T00:00:00Z",
        }
    }
    usage = fetch_project_usage(SecretStr(KEY), "p1", client(200, body, seen))
    assert usage.transfer_bytes == 480_000_000
    assert usage.period_start == datetime(2026, 11, 20, tzinfo=UTC)
    assert usage.period_end == datetime(2026, 12, 1, tzinfo=UTC)
    assert seen[0].url.path == "/projects/p1"
    assert seen[0].headers["authorization"] == f"Bearer {KEY}"


def test_missing_or_bad_period_dates_are_none() -> None:
    body = {"project": {"data_transfer_bytes": 5, "consumption_period_start": "not a date"}}
    usage = fetch_project_usage(SecretStr(KEY), "p1", client(200, body))
    assert (usage.period_start, usage.period_end) == (None, None)


@pytest.mark.parametrize(
    ("status", "body"),
    [(401, {"message": "unauthorized"}), (200, {"project": {}}), (200, {})],
)
def test_errors_never_carry_the_key(status: int, body: object) -> None:
    with pytest.raises(NeonApiError) as caught:
        fetch_project_usage(SecretStr(KEY), "p1", client(status, body))
    assert KEY not in str(caught.value)


def test_network_failure_is_a_clean_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    http = httpx.Client(base_url="https://neon.test", transport=httpx.MockTransport(handler))
    with pytest.raises(NeonApiError, match="unreachable"):
        fetch_project_usage(SecretStr(KEY), "p1", http)
