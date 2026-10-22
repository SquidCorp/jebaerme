"""Application settings loaded from the environment."""

from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

_API_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_API_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "dev"
    OPENROUTER_API_KEY: SecretStr | None = None

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

    @field_validator("OPENROUTER_API_KEY", mode="before")
    @classmethod
    def strip_openrouter_api_key(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().strip("'\"")
        return value

    def openrouter_api_key(self) -> str | None:
        if self.OPENROUTER_API_KEY is None:
            return None
        return self.OPENROUTER_API_KEY.get_secret_value()


env = Settings()
