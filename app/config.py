"""Environment configuration (SPECIFICATION.md §2, 12-factor)."""

from __future__ import annotations

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SEVERITY_MODES = ("strict", "normal", "lenient")


class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    llm_model: str = Field(description="Model id used by agents")
    llm_api_key: str = Field(description="Provider key")
    langsmith_api_key: str | None = Field(default=None)
    langsmith_project: str = Field(default="code-review-agent")
    chroma_path: str = Field(default="./.chroma")
    embedding_model: str = Field(default="text-embedding-3-small")
    max_diff_lines: int = Field(default=3000, gt=0)
    review_severity: str = Field(default="normal")

    @field_validator("llm_model", "llm_api_key")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("langsmith_api_key")
    @classmethod
    def _empty_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("review_severity")
    @classmethod
    def _severity(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in SEVERITY_MODES:
            raise ValueError(
                f"must be one of {', '.join(SEVERITY_MODES)} (got {value!r})"
            )
        return value


def load_settings(env_file: str | None = ".env") -> Settings:
    """Load and validate settings from env vars + .env.

    Args:
        env_file: dotenv file to read, or ``None`` to use env vars only.

    Raises:
        ConfigError: on any validation failure (caller exits with code 2).
    """
    try:
        return Settings(_env_file=env_file)
    except ValidationError as exc:
        problems = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"]) or "settings"
            problems.append(f"{loc}: {err['msg']}")
        raise ConfigError("; ".join(problems)) from exc
