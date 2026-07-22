from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.cors import normalize_cors_origins


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "URIM"
    engine_name: str = "Kairos"
    app_version: str = "0.1.0"
    default_locale: str = "fr-CD"
    default_currency: str = "CDF"
    database_url: str | None = None
    redis_url: str | None = None
    object_storage_url: str | None = None
    enable_live: bool = False
    enable_real_betting: bool = False
    allow_test_fixtures: bool = False
    allow_production_mocks: bool = False
    cors_origins: str = (
        "http://localhost:3000,https://urim.pro,"
        "https://www.urim.pro,https://urim-web.onrender.com"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> tuple[str, ...]:
        return normalize_cors_origins(self.cors_origins)


settings = Settings()
