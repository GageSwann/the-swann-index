"""Read the project's network transfer for the current period from Neon's API (#140, #179).

One GET of the project's details (`/projects/{id}`): `data_transfer_bytes` is Neon's
running total for the current billing period, every branch included, reset when a new
period starts. Neon notes these usage fields are "not intended for billing", so this is
an early warning, not the bill. The key goes only into the request header, never into
logs or errors.
"""

from dataclasses import dataclass
from datetime import datetime

import httpx
from pydantic import SecretStr

from tsi.ingest.transform.timeutil import parse_utc

BASE_URL = "https://console.neon.tech/api/v2"
TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class NeonApiError(RuntimeError):
    """Neon didn't answer with the project's usage. The message never holds the key."""


@dataclass(frozen=True)
class ProjectUsage:
    transfer_bytes: int
    period_start: datetime | None  # Neon's consumption period, when it sends one
    period_end: datetime | None


def fetch_project_usage(
    api_key: SecretStr, project_id: str, http: httpx.Client | None = None
) -> ProjectUsage:
    client = http or httpx.Client(base_url=BASE_URL, timeout=TIMEOUT)
    headers = {
        "Authorization": f"Bearer {api_key.get_secret_value()}",
        "Accept": "application/json",
    }
    try:
        response = client.get(f"/projects/{project_id}", headers=headers)
    except httpx.HTTPError as exc:
        raise NeonApiError(f"Neon API unreachable ({type(exc).__name__})") from None
    finally:
        if http is None:
            client.close()
    if response.status_code != 200:
        raise NeonApiError(f"Neon API answered HTTP {response.status_code}")
    project = response.json().get("project") or {}
    if not isinstance(project.get("data_transfer_bytes"), int):
        raise NeonApiError("Neon's project details have no data_transfer_bytes")
    return ProjectUsage(
        transfer_bytes=project["data_transfer_bytes"],
        period_start=_time(project.get("consumption_period_start")),
        period_end=_time(project.get("consumption_period_end")),
    )


def _time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return parse_utc(value)
    except ValueError:
        return None
