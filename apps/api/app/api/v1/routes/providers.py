from fastapi import APIRouter

from app.modules.providers.sandbox import build_sandbox_provider_status_response
from app.schemas.common import SkeletonCollectionResponse, empty_collection
from app.schemas.providers import (
    ProviderReadinessResponse,
    SandboxProviderStatusResponse,
    build_provider_readiness_response,
)

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=SkeletonCollectionResponse)
def list_providers() -> SkeletonCollectionResponse:
    return empty_collection(
        "providers",
        [
            "Provider connectors are disabled in Phase 23.",
            "Provider onboarding gate blocks real provider activation.",
            "API-Football is not connected.",
            "API-Football read-only adapter is disabled by default.",
            "API-Football test transport contracts are internal and non-production only.",
            "API-Football smoke client is internal, env-gated and disabled by default.",
            "API-Football manual smoke runner is local-only and is not exposed through FastAPI.",
            "API-Football local smoke runbook is documentation-only and does not execute provider calls.",
            "API-Football local HTTP smoke harness is script-only and is not exposed through FastAPI.",
            "API-Football first real local smoke protocol is documentation-only and is not an endpoint.",
            "API-Football local secret and environment preflight is script-only and is not exposed through FastAPI.",
            "Provider secret safety is prepared without exposing future env names or values.",
            "Provider preflight review is blocked until future audit approval.",
            "Real provider adapter shell is blocked and has no URL, credential or HTTP client.",
            "Provider activation readiness final gate blocks production provider activation.",
            "Sandbox provider status is informational and non-production.",
            "No bookmaker integration is exposed.",
        ],
    )


@router.get("/readiness", response_model=ProviderReadinessResponse)
def provider_readiness() -> ProviderReadinessResponse:
    return build_provider_readiness_response()


@router.get("/sandbox/status", response_model=SandboxProviderStatusResponse)
def provider_sandbox_status() -> SandboxProviderStatusResponse:
    return build_sandbox_provider_status_response()
