from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
