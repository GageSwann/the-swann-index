"""`tsi neon transfer`: skips without a key; prints one JSON reading with one."""

import json
from datetime import UTC, datetime

from pydantic import SecretStr
from typer.testing import CliRunner

from tsi.cli import neon
from tsi.cli.main import app
from tsi.config import Settings
from tsi.ops.neon_api import ProjectUsage


def settings(key: str | None, project: str | None) -> Settings:
    return Settings(
        database_url=SecretStr("postgresql://x"),
        neon_api_key=SecretStr(key) if key else None,
        neon_project_id=project,
        _env_file=None,
    )


def test_skips_without_key_or_project(monkeypatch) -> None:
    for key, project in ((None, "p1"), ("fakekey", None)):
        monkeypatch.setattr(neon, "load_settings", lambda k=key, p=project: settings(k, p))
        result = CliRunner().invoke(app, ["neon", "transfer"])
        assert result.exit_code == 2
        assert "Skipped: NEON_API_KEY" in result.output


def test_prints_the_reading_as_json(monkeypatch) -> None:
    monkeypatch.setattr(neon, "load_settings", lambda: settings("fakekey", "p1"))
    start = datetime(2026, 11, 1, tzinfo=UTC)
    monkeypatch.setattr(
        neon,
        "fetch_project_usage",
        lambda key, project: ProjectUsage(10_000_000, start, datetime(2030, 1, 1, tzinfo=UTC)),
    )
    result = CliRunner().invoke(app, ["neon", "transfer", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["used_bytes"] == 10_000_000 and data["status"] == "ok"
    assert "fakekey" not in result.stdout
