"""Application settings loaded from the environment."""

import os
from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

_API_ROOT = Path(__file__).resolve().parents[3]

_LANGSMITH_ENV_KEYS = (
    "LANGSMITH_TRACING",
    "LANGSMITH_ENDPOINT",
    "LANGSMITH_API_KEY",
    "LANGSMITH_AGENT_ID",
    "LANGSMITH_AGENT_ENVIRONMENT",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_API_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "dev"
    OPENROUTER_API_KEY: SecretStr | None = None
    LANGSMITH_TRACING: bool = False
    LANGSMITH_ENDPOINT: str | None = None
    LANGSMITH_API_KEY: SecretStr | None = None
    LANGSMITH_AGENT_ID: str | None = None
    LANGSMITH_AGENT_ENVIRONMENT: str | None = None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # apps/api/.env beats a stale OPENROUTER_API_KEY exported in the shell.
        return init_settings, dotenv_settings, env_settings, file_secret_settings

    @field_validator("OPENROUTER_API_KEY", "LANGSMITH_API_KEY", mode="before")
    @classmethod
    def strip_secret(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().strip("'\"")
        return value

    def openrouter_api_key(self) -> str | None:
        if self.OPENROUTER_API_KEY is None:
            return None
        return self.OPENROUTER_API_KEY.get_secret_value()

    def apply_langsmith_env(self) -> None:
        """Export LangSmith settings so the SDK can trace create_agent runs."""
        for key in _LANGSMITH_ENV_KEYS:
            os.environ.pop(key, None)
        if not self.LANGSMITH_TRACING:
            return
        os.environ["LANGSMITH_TRACING"] = "true"
        if self.LANGSMITH_ENDPOINT:
            os.environ["LANGSMITH_ENDPOINT"] = self.LANGSMITH_ENDPOINT
        if self.LANGSMITH_API_KEY is not None:
            os.environ["LANGSMITH_API_KEY"] = self.LANGSMITH_API_KEY.get_secret_value()
        if self.LANGSMITH_AGENT_ID:
            os.environ["LANGSMITH_AGENT_ID"] = self.LANGSMITH_AGENT_ID
        if self.LANGSMITH_AGENT_ENVIRONMENT:
            os.environ["LANGSMITH_AGENT_ENVIRONMENT"] = self.LANGSMITH_AGENT_ENVIRONMENT


env = Settings()
env.apply_langsmith_env()
