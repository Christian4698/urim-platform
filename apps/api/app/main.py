from fastapi import FastAPI

from app.api.v1.router import include_api_v1
from app.core.config import settings
from app.core.constants import (
    API_PHASE,
    DATABASE_OK,
    DISABLED_STATUS,
    PHASE_LIVE_ENABLED,
    PHASE_REAL_BETTING_ENABLED,
)
from app.core.security import (
    add_cors,
    add_public_error_handlers,
    add_security_headers,
)
from app.db.session import get_database_status
from app.modules.kairos.rate_limit import get_redis_rate_limit_status
from app.schemas.health import HealthResponse, ReadinessResponse, VersionResponse

DEVELOPMENT_APP_ENVS = frozenset({"development", "dev", "local", "test"})


def _openapi_paths(app_env: str) -> tuple[str | None, str | None, str | None]:
    if app_env.strip().lower() in DEVELOPMENT_APP_ENVS:
        return "/openapi.json", "/docs", "/redoc"
    return None, None, None


openapi_url, docs_url, redoc_url = _openapi_paths(settings.app_env)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="URIM public read-only system API for platform availability.",
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_tags=[
        {"name": "system", "description": "Health, readiness and capabilities."},
        {"name": "fixtures", "description": "Read-only fixture skeletons for future phases."},
        {"name": "predictions", "description": "Read-only prediction ledger skeletons."},
        {"name": "tickets", "description": "Virtual/internal Bet Center ticket skeletons."},
        {"name": "providers", "description": "Disabled provider connector skeletons."},
        {
            "name": "sports-data",
            "description": "Programme B1 sports data exposed read-only.",
        },
        {
            "name": "kairos",
            "description": (
                "B2.1 pre-match analysis from existing database observations."
            ),
        },
        {"name": "post-match", "description": "Verified outcome skeletons for future learning."},
    ],
)

add_cors(app, settings.cors_origin_list)
add_security_headers(app)
add_public_error_handlers(app)
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
    database_status = get_database_status()
    redis_status = get_redis_rate_limit_status()
    return ReadinessResponse(
        ready=(
            database_status == DATABASE_OK
            and redis_status == DATABASE_OK
        ),
        phase=API_PHASE,
        dependencies={
            "database": database_status,
            "redis": redis_status,
            "sports_providers": (
                "ready"
                if settings.api_football_runtime_enabled
                else DISABLED_STATUS
            ),
            "bookmakers": DISABLED_STATUS,
            "ml_models": DISABLED_STATUS,
            "live": DISABLED_STATUS,
            "real_betting": DISABLED_STATUS,
            "prediction_creation": DISABLED_STATUS,
        },
    )
