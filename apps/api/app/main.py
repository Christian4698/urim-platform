from fastapi import FastAPI

from app.api.v1.router import include_api_v1
from app.core.config import settings
from app.core.constants import (
    API_PHASE,
    DISABLED_STATUS,
    NOT_REQUIRED_STATUS,
    PHASE_LIVE_ENABLED,
    PHASE_REAL_BETTING_ENABLED,
)
from app.core.security import add_security_headers
from app.db.session import get_database_status
from app.schemas.health import HealthResponse, ReadinessResponse, VersionResponse

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="URIM Phase 16 API-Football read-only adapter for the Kairos engine.",
    openapi_tags=[
        {"name": "system", "description": "Health, readiness and capabilities."},
        {"name": "fixtures", "description": "Read-only fixture skeletons for future phases."},
        {"name": "predictions", "description": "Read-only prediction ledger skeletons."},
        {"name": "tickets", "description": "Virtual/internal Bet Center ticket skeletons."},
        {"name": "providers", "description": "Disabled provider connector skeletons."},
        {"name": "post-match", "description": "Verified outcome skeletons for future learning."},
    ],
)

add_security_headers(app)
include_api_v1(app)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        engine_name=settings.engine_name,
        phase=API_PHASE,
    )


@app.get("/version", response_model=VersionResponse, tags=["system"])
def version() -> VersionResponse:
    return VersionResponse(
        app_name=settings.app_name,
        engine_name=settings.engine_name,
        version=settings.app_version,
        default_locale=settings.default_locale,
        default_currency=settings.default_currency,
        live_enabled=PHASE_LIVE_ENABLED,
        real_betting_enabled=PHASE_REAL_BETTING_ENABLED,
    )


@app.get("/readiness", response_model=ReadinessResponse, tags=["system"])
def readiness() -> ReadinessResponse:
    return ReadinessResponse(
        ready=True,
        phase=API_PHASE,
        dependencies={
            "database": get_database_status(),
            "redis": NOT_REQUIRED_STATUS,
            "sports_providers": DISABLED_STATUS,
            "bookmakers": DISABLED_STATUS,
            "ml_models": DISABLED_STATUS,
            "live": DISABLED_STATUS,
            "real_betting": DISABLED_STATUS,
            "prediction_creation": DISABLED_STATUS,
        },
    )
