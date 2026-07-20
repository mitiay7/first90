from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_base_url: str = "http://localhost:8080"
    database_url: str = "sqlite:///./data/first90.db"
    demo_mode: bool = True
    secret_key: str = Field(default="development-secret-change-before-production")
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-sol"
    telegram_bot_token: str | None = None
    telegram_bot_username: str | None = None
    telegram_webhook_secret: str = "development-webhook-secret"
    public_host: str = "first90.hub.lea-dev.site"
    studio_host: str = "first90-studio.hub.lea-dev.site"
    api_host: str = "first90-api.hub.lea-dev.site"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
