from fastapi import FastAPI

from app.api.v1.router import include_api_v1
from app.core.config import settings
from app.core.constants import API_PHASE, DISABLED_PHASE_3
from app.core.security import add_security_headers
from app.db.session import get_database_status
from app.schemas.health import HealthResponse, ReadinessResponse, VersionResponse

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="URIM Phase 3 API foundation for the Kairos engine.",
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
        live_enabled=False,
        real_betting_enabled=False,
    )


@app.get("/readiness", response_model=ReadinessResponse, tags=["system"])
def readiness() -> ReadinessResponse:
    return ReadinessResponse(
        ready=True,
        phase=API_PHASE,
        dependencies={
            "database": get_database_status(),
            "redis": "not_required_phase_3",
            "sports_providers": DISABLED_PHASE_3,
            "bookmakers": DISABLED_PHASE_3,
            "ml_models": DISABLED_PHASE_3,
            "live": DISABLED_PHASE_3,
            "real_betting": DISABLED_PHASE_3,
            "prediction_creation": DISABLED_PHASE_3,
        },
    )
