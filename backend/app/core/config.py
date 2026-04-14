from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_KEYS = {"change-this-secret-key", "secret", "changeme", "", "your-secret-key"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Redline API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "change-this-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "postgresql+psycopg://redline:redline@localhost:5432/redline"
    DATABASE_SCHEMA: str = "redline"

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]
    MEDIA_DIR: str = "media"
    MEDIA_URL: str = "/media"

    # Redis Cache Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_ENABLED: bool = True
    REDIS_CACHE_TTL_REPORTS: int = 900  # 15 minutes
    REDIS_CACHE_TTL_LISTS: int = 1800  # 30 minutes
    REDIS_CACHE_TTL_ENTITIES: int = 3600  # 1 hour
    REDIS_CACHE_TTL_SEARCH: int = 600  # 10 minutes
    REDIS_CACHE_TTL_SETTINGS: int = 86400  # 24 hours

    @field_validator("SECRET_KEY", mode="after")
    @classmethod
    def secret_key_must_be_set(cls, value: str) -> str:
        if value.strip().lower() in _INSECURE_KEYS or len(value.strip()) < 32:
            raise ValueError(
                "\n\n"
                "  ╔══════════════════════════════════════════════════════════╗\n"
                "  ║  SECRET_KEY is not set or is insecure.                  ║\n"
                "  ║                                                          ║\n"
                "  ║  Set a strong value in your .env file:                   ║\n"
                "  ║                                                          ║\n"
                '  ║    python -c "import secrets; print(secrets.token_hex(32))"\n'
                "  ║                                                          ║\n"
                "  ║  Then add to .env:  SECRET_KEY=<generated value>         ║\n"
                "  ╚══════════════════════════════════════════════════════════╝\n"
            )
        return value

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, value: Any) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            raw = value.strip()
            if raw.startswith("[") and raw.endswith("]"):
                import json

                parsed = json.loads(raw)
                if not isinstance(parsed, list):
                    raise ValueError("ALLOWED_ORIGINS JSON must be a list")
                return [str(v).strip() for v in parsed if str(v).strip()]
            return [item.strip() for item in raw.split(",") if item.strip()]
        raise ValueError("Invalid ALLOWED_ORIGINS value")

    @property
    def media_path(self) -> Path:
        return Path(self.MEDIA_DIR)


settings = Settings()
