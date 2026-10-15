"""Application settings. The ONLY module that reads environment variables.

Values come from real environment variables first, then `backend/.env`.
Secrets are `SecretStr`, so they are masked in repr/str/logs; call
`.get_secret_value()` only at the point of use (DB engine, HTTP header).
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# src/tsi/config.py -> backend/
BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = BACKEND_DIR / ".env"


class ConfigError(RuntimeError):
    """Settings are missing or invalid. The message never contains values."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        env_ignore_empty=True,  # `NAME=` with no value counts as unset
    )

    cfbd_api_key: SecretStr
    database_url: SecretStr
    # Direct (non-pooled) connection for Alembic migrations; falls back to database_url.
    database_url_direct: SecretStr | None = None
    cfbd_monthly_call_budget: int = Field(default=980, ge=0)
    tsi_cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    # Raw CFBD response cache (gitignored).
    tsi_cache_dir: Path = BACKEND_DIR / ".cache"

    @field_validator("cfbd_api_key", "database_url")
    @classmethod
    def _not_blank(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("is empty")
        return value

    @field_validator("tsi_cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def migration_database_url(self) -> SecretStr:
        return self.database_url_direct or self.database_url


def load_settings(env_file: Path | None = DEFAULT_ENV_FILE) -> Settings:
    """Build settings, converting validation errors into a value-free ConfigError."""
    try:
        return Settings(_env_file=env_file)
    except ValidationError as exc:
        raise ConfigError(_describe_errors(exc)) from None


@lru_cache
def get_settings() -> Settings:
    """Cached settings for app code. Tests should call `load_settings` directly."""
    return load_settings()


def _describe_errors(exc: ValidationError) -> str:
    # Pydantic's default message includes the input values; list names and reasons only.
    lines = [
        f"  {str(err['loc'][0]).upper()}: {'missing' if err['type'] == 'missing' else err['msg']}"
        for err in exc.errors()
    ]
    return (
        "Invalid TSI configuration (set these in backend/.env or the environment):\n"
        + "\n".join(lines)
    )
