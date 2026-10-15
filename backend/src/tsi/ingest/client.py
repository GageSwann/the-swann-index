"""Thin CFBD HTTP client: disk cache first, then a budget-checked API request.

Every loader goes through `CfbdClient.get`. The API key is sent only as a request
header; it is never logged, cached, or included in error messages.
"""

import logging
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any, Self

import httpx
from pydantic import SecretStr

from tsi.ingest.cache import DiskCache
from tsi.ingest.freshness import is_fresh
from tsi.ingest.ledger import CallLedger, CallRecord

FreshnessRule = Callable[[Mapping[str, Any], datetime, datetime], bool]

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.collegefootballdata.com"


class CfbdError(RuntimeError):
    """A CFBD request failed."""


class BudgetExceededError(CfbdError):
    """This month's call budget is used up; no request was sent."""


class CfbdClient:
    def __init__(
        self,
        *,
        api_key: SecretStr,
        cache: DiskCache,
        ledger: CallLedger,
        monthly_budget: int,
        http: httpx.Client | None = None,
        base_url: str = DEFAULT_BASE_URL,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        freshness: FreshnessRule = is_fresh,
    ) -> None:
        self._api_key = api_key
        self._cache = cache
        self._ledger = ledger
        self._budget = monthly_budget
        self._http = http or httpx.Client(base_url=base_url, timeout=30.0)
        self._clock = clock
        self._is_fresh = freshness

    def get(
        self, endpoint: str, params: Mapping[str, Any] | None = None, *, refresh: bool = False
    ) -> Any:
        """Return the JSON body for `endpoint`.

        Served from cache when the entry is still fresh (see `tsi.ingest.freshness`);
        `refresh=True` always re-fetches.
        """
        clean = {k: v for k, v in (params or {}).items() if v is not None}
        if not refresh:
            cached = self._cache.get(endpoint, clean)
            if cached is not None and self._is_fresh(clean, cached.fetched_at, self._clock()):
                self._record(endpoint, clean, from_cache=True, status="ok", data=cached.data)
                return cached.data

        self._check_budget()
        data = self._fetch(endpoint, clean)
        self._cache.put(endpoint, clean, data, fetched_at=self._clock())
        self._record(endpoint, clean, from_cache=False, status="ok", data=data)
        return data

    def _check_budget(self) -> None:
        used = self._ledger.calls_this_month(self._clock())
        if used >= self._budget:
            raise BudgetExceededError(
                f"CFBD monthly call budget reached ({used}/{self._budget}). "
                "Wait for next month or raise CFBD_MONTHLY_CALL_BUDGET."
            )

    def _fetch(self, endpoint: str, params: dict[str, Any]) -> Any:
        headers = {
            "Authorization": f"Bearer {self._api_key.get_secret_value()}",
            "Accept": "application/json",
        }
        try:
            response = self._http.get(endpoint, params=params, headers=headers)
        except httpx.HTTPError as exc:
            self._record(endpoint, params, from_cache=False, status="error")
            raise CfbdError(f"CFBD request to {endpoint} failed: {type(exc).__name__}") from exc

        if response.status_code != httpx.codes.OK:
            self._record(endpoint, params, from_cache=False, status="error")
            raise CfbdError(f"CFBD {endpoint} returned HTTP {response.status_code}")

        remaining = response.headers.get("X-CallLimit-Remaining")
        logger.info("CFBD %s %s -> 200 (calls remaining: %s)", endpoint, params, remaining)
        return response.json()

    def _record(
        self,
        endpoint: str,
        params: dict[str, Any],
        *,
        from_cache: bool,
        status: str,
        data: Any = None,
    ) -> None:
        self._ledger.record(
            CallRecord(
                endpoint=endpoint,
                params=params,
                fetched_at=self._clock(),
                from_cache=from_cache,
                status=status,
                row_count=len(data) if isinstance(data, list) else None,
            )
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
