from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'AgriPulse AI API'
    environment: str = 'development'
    secret_key: str = 'change-me'
    access_token_expire_minutes: int = 60 * 24
    database_url: str = '******db:5432/agripulse'
    redis_url: str = 'redis://redis:6379/0'
    allowed_origins: str = 'http://localhost:3000'


settings = Settings()
