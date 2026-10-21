"""Application settings loaded from the environment."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_API_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_API_ROOT / ".env",
        extra="ignore",
    )

    APP_ENV: str = "dev"


env = Settings()
