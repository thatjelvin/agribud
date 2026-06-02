from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "AgriPulse AI API"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://app:app@db:5432/agripulse"
    redis_url: str = "redis://redis:6379/0"

    jwt_secret: str = "change-this-to-a-long-random-secret"
    jwt_expires_minutes: int = 60 * 24
    jwt_cookie_name: str = "access_token"

    cors_origins: str = "http://localhost:3000"

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.groq.com/openai/v1"

    yield_model: str = "v1-statistical"
    geospatial_provider: str = "mock"
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"

    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


settings = Settings()
