from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    app_name: str
    engine_name: str
    phase: str

    model_config = ConfigDict(extra="forbid")


class VersionResponse(BaseModel):
    app_name: str
    engine_name: str
    version: str
    default_locale: str
    default_currency: str
    live_enabled: bool
    real_betting_enabled: bool

    model_config = ConfigDict(extra="forbid")


class ReadinessResponse(BaseModel):
    ready: bool
    phase: str
    dependencies: dict[str, str]

    model_config = ConfigDict(extra="forbid")
