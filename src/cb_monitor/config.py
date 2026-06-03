"""Application settings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CB_",
        extra="ignore",
        str_strip_whitespace=True,
    )

    cookie: SecretStr | None = None
    cookie_file: Path | None = None
    cf_clearance: SecretStr | None = None
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    )
    timeout_seconds: float = Field(default=15.0, gt=0.0, le=60.0)
    retry_attempts: int = Field(default=3, ge=1, le=8)
    proxy_url: str | None = None
    mpv_path: str = Field(default="mpv", min_length=1)
    log_level: str = Field(default="INFO", min_length=1)
    base_url: str = "https://chaturbate.com"
    followed_path: str = "/followed-cams/"
    log_file: Path | None = None

    @field_validator(
        "cookie",
        "cookie_file",
        "cf_clearance",
        "proxy_url",
        mode="before",
    )
    @classmethod
    def empty_string_as_none(cls, value: Any) -> Any:
        """Treat blank .env values as unset to support example files."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def require_cookie_source(self) -> Settings:
        """Fail fast when no authentication source is configured."""
        if self.cookie is None and self.cookie_file is None:
            msg = "CB_COOKIE 或 CB_COOKIE_FILE 必须至少设置一个。"
            raise ValueError(msg)
        return self
