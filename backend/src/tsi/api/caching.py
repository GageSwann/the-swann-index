"""HTTP caching for a read-only API whose data changes once a day (the 10:00 UTC run).

- `Cache-Control` per path prefix: successful GETs are public and short-lived with a
  long stale-while-revalidate window; `/matchup` is cached as long as its live inputs;
  errors are `no-store`.
- Strong `ETag` = hash of the JSON body; a matching `If-None-Match` gets an empty 304.
"""

import hashlib

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

DEFAULT_POLICY = "public, max-age=300, stale-while-revalidate=86400"
POLICIES = {
    "/matchup": "public, max-age=3600",  # same TTL as the in-process live-inputs cache
    "/docs": "no-cache",
    "/redoc": "no-cache",
}
NO_STORE = "no-store"


def cache_policy(path: str, status: int) -> str:
    if status >= 400:
        return NO_STORE
    for prefix, policy in POLICIES.items():
        if path == prefix or path.startswith(prefix + "/"):
            return policy
    return DEFAULT_POLICY


def etag(body: bytes) -> str:
    return '"' + hashlib.sha256(body).hexdigest()[:32] + '"'


class CachingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        if request.method not in ("GET", "HEAD"):
            return response
        policy = cache_policy(request.url.path, response.status_code)
        if response.status_code != 200 or "json" not in response.headers.get("content-type", ""):
            response.headers["Cache-Control"] = policy
            return response
        body = b"".join([chunk async for chunk in response.body_iterator])
        tag = etag(body)
        if _matches(request.headers.get("if-none-match"), tag):
            return Response(status_code=304, headers={"Cache-Control": policy, "ETag": tag})
        headers = {k: v for k, v in response.headers.items() if k.lower() != "content-length"}
        headers |= {"Cache-Control": policy, "ETag": tag}
        return Response(body, status_code=200, headers=headers)


def _matches(if_none_match: str | None, tag: str) -> bool:
    if not if_none_match:
        return False
    return if_none_match.strip() == "*" or tag in [t.strip() for t in if_none_match.split(",")]
