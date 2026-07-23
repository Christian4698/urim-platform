from pydantic import Field, SecretStr, field_validator
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
    api_football_key: SecretStr | None = None
    api_football_enabled: bool = False
    api_football_priority_competitions: str = ""
    api_football_season: int | None = Field(default=None, ge=1900, le=2100)
    api_football_request_timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        le=30,
    )
    api_football_max_retries: int = Field(default=2, ge=0, le=3)
    api_football_requests_per_minute: int = Field(default=10, ge=1, le=1_200)
    api_football_max_requests_per_sync: int = Field(default=10, ge=1, le=100)
    api_football_upcoming_days: int = Field(default=7, ge=1, le=30)
    api_football_freshness_minutes: int = Field(
        default=180,
        ge=1,
        le=10_080,
    )
    cors_origins: str = (
        "http://localhost:3000,https://urim.pro,"
        "https://www.urim.pro,https://urim-web.onrender.com"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("api_football_priority_competitions")
    @classmethod
    def validate_priority_competitions(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            return ""
        try:
            ids = tuple(
                int(item.strip())
                for item in normalized.split(",")
                if item.strip()
            )
        except ValueError as exc:
            raise ValueError(
                "API-Football priority competition IDs must be integers."
            ) from exc
        if any(item <= 0 for item in ids):
            raise ValueError(
                "API-Football priority competition IDs must be positive."
            )
        if len(ids) > 10 or len(set(ids)) != len(ids):
            raise ValueError(
                "API-Football priority competitions must contain at most "
                "10 unique IDs."
            )
        return ",".join(str(item) for item in ids)

    @property
    def cors_origin_list(self) -> tuple[str, ...]:
        return normalize_cors_origins(self.cors_origins)

    @property
    def api_football_key_configured(self) -> bool:
        return bool(
            self.api_football_key
            and self.api_football_key.get_secret_value().strip()
        )

    @property
    def api_football_runtime_enabled(self) -> bool:
        return self.api_football_enabled and self.api_football_key_configured

    @property
    def api_football_priority_competition_ids(self) -> tuple[int, ...]:
        return tuple(
            int(value.strip())
            for value in self.api_football_priority_competitions.split(",")
            if value.strip()
        )


settings = Settings()
