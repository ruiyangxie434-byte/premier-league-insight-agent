from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_VERSION = "0.11.0"


class Settings(BaseSettings):
    app_name: str = "Premier League Insight Agent API"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api"
    frontend_origins: str = "http://localhost:3000"
    database_url: str = "sqlite:///./pl_geo_analytics.db"
    auto_create_database: bool = True
    seed_sample_data: bool = True
    dashscope_api_key: str | None = None
    qwen_base_url: str = (
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    qwen_model: str = "qwen-plus"
    qwen_timeout_seconds: float = 20.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.frontend_origins.split(",")
            if origin.strip()
        ]

    @property
    def app_version(self) -> str:
        """Return the code version so an older local .env cannot mask upgrades."""
        return APP_VERSION

    @property
    def qwen_configured(self) -> bool:
        return bool(
            self.dashscope_api_key
            and self.dashscope_api_key.strip()
            and self.qwen_base_url.strip()
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
