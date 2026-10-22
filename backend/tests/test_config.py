from pathlib import Path

import pytest

from tsi.config import ConfigError, load_settings

SECRET_KEY = "cfbd-secret-value-123"
SECRET_URL = "postgresql://user:hunter2@ep-test-pooler.neon.tech/neondb?sslmode=require"
ENV_NAMES = [
    "CFBD_API_KEY",
    "DATABASE_URL",
    "DATABASE_URL_DIRECT",
    "CFBD_MONTHLY_CALL_BUDGET",
    "TSI_CORS_ORIGINS",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


@pytest.fixture
def required_env(clean_env: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    clean_env.setenv("CFBD_API_KEY", SECRET_KEY)
    clean_env.setenv("DATABASE_URL", SECRET_URL)
    return clean_env


def test_loads_from_environment_with_defaults(required_env: pytest.MonkeyPatch) -> None:
    settings = load_settings(env_file=None)

    assert settings.cfbd_api_key.get_secret_value() == SECRET_KEY
    assert settings.cfbd_monthly_call_budget == 980
    assert settings.tsi_cors_origins == ["http://localhost:3000"]


def test_loads_from_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(f"CFBD_API_KEY={SECRET_KEY}\nDATABASE_URL={SECRET_URL}\n")

    settings = load_settings(env_file=env_file)

    assert settings.database_url.get_secret_value() == SECRET_URL


def test_secrets_are_masked_in_repr(required_env: pytest.MonkeyPatch) -> None:
    settings = load_settings(env_file=None)

    assert SECRET_KEY not in repr(settings)
    assert "hunter2" not in str(settings)


def test_missing_variable_names_it_without_leaking_values(
    clean_env: pytest.MonkeyPatch,
) -> None:
    clean_env.setenv("CFBD_API_KEY", SECRET_KEY)

    with pytest.raises(ConfigError) as exc_info:
        load_settings(env_file=None)

    message = str(exc_info.value)
    assert "DATABASE_URL: missing" in message
    assert SECRET_KEY not in message


def test_cfbd_key_is_only_required_to_call_cfbd(clean_env: pytest.MonkeyPatch) -> None:
    clean_env.setenv("DATABASE_URL", SECRET_URL)  # the API host's settings

    settings = load_settings(env_file=None)

    assert settings.cfbd_api_key is None
    with pytest.raises(ConfigError, match="CFBD_API_KEY: missing") as exc_info:
        settings.require_cfbd_key()
    assert "hunter2" not in str(exc_info.value)


def test_blank_secret_is_rejected(required_env: pytest.MonkeyPatch) -> None:
    required_env.setenv("CFBD_API_KEY", "   ")

    with pytest.raises(ConfigError, match="CFBD_API_KEY"):
        load_settings(env_file=None)


def test_invalid_budget_error_does_not_echo_value(required_env: pytest.MonkeyPatch) -> None:
    required_env.setenv("CFBD_MONTHLY_CALL_BUDGET", "-5")

    with pytest.raises(ConfigError) as exc_info:
        load_settings(env_file=None)

    message = str(exc_info.value)
    assert "CFBD_MONTHLY_CALL_BUDGET" in message
    assert SECRET_KEY not in message and "hunter2" not in message


def test_empty_optional_value_counts_as_unset(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"CFBD_API_KEY={SECRET_KEY}\nDATABASE_URL={SECRET_URL}\nDATABASE_URL_DIRECT=\n"
    )

    settings = load_settings(env_file=env_file)

    assert settings.migration_database_url.get_secret_value() == SECRET_URL


def test_cors_origins_split_on_commas(required_env: pytest.MonkeyPatch) -> None:
    required_env.setenv("TSI_CORS_ORIGINS", "http://localhost:3000, https://tsi.example.com")

    settings = load_settings(env_file=None)

    assert settings.tsi_cors_origins == ["http://localhost:3000", "https://tsi.example.com"]


def test_migration_url_falls_back_to_pooled(required_env: pytest.MonkeyPatch) -> None:
    assert load_settings(env_file=None).migration_database_url.get_secret_value() == SECRET_URL

    required_env.setenv("DATABASE_URL_DIRECT", "postgresql://direct")

    assert (
        load_settings(env_file=None).migration_database_url.get_secret_value()
        == "postgresql://direct"
    )
