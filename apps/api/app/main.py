from fastapi import FastAPI

from app.core.config import settings
from app.schemas.health import HealthResponse, ReadinessResponse, VersionResponse

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="URIM Phase 1 API skeleton for the Kairos engine.",
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        engine_name=settings.engine_name,
        phase="phase-1-app-skeleton",
    )


@app.get("/version", response_model=VersionResponse, tags=["system"])
def version() -> VersionResponse:
    return VersionResponse(
        app_name=settings.app_name,
        engine_name=settings.engine_name,
        version=settings.app_version,
        default_locale=settings.default_locale,
        default_currency=settings.default_currency,
        live_enabled=settings.enable_live,
        real_betting_enabled=settings.enable_real_betting,
    )


@app.get("/readiness", response_model=ReadinessResponse, tags=["system"])
def readiness() -> ReadinessResponse:
    return ReadinessResponse(
        ready=True,
        phase="phase-1-app-skeleton",
        dependencies={
            "database": "not_required_phase_1",
            "redis": "not_required_phase_1",
            "sports_providers": "disabled_phase_1",
            "bookmakers": "disabled_phase_1",
            "ml_models": "disabled_phase_1",
        },
    )
