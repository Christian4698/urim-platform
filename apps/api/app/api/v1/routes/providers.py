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
            "Provider connectors are disabled in Phase 13.",
            "Provider onboarding gate blocks real provider activation.",
            "API-Football is not connected.",
            "Provider secret safety is prepared without exposing future env names or values.",
            "Provider preflight review is blocked until future audit approval.",
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
