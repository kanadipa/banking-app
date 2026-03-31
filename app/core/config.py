from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Banking API"
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    api_key: str = Field(default="")
    database_url: str = Field(default="")


settings = Settings()
