from fastapi import APIRouter

from app.schemas.common import SkeletonCollectionResponse, empty_collection
from app.schemas.providers import ProviderReadinessResponse, build_provider_readiness_response

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=SkeletonCollectionResponse)
def list_providers() -> SkeletonCollectionResponse:
    return empty_collection(
        "providers",
        [
            "Provider connectors are disabled in Phase 6.",
            "API-Football is not connected.",
            "No bookmaker integration is exposed.",
        ],
    )


@router.get("/readiness", response_model=ProviderReadinessResponse)
def provider_readiness() -> ProviderReadinessResponse:
    return build_provider_readiness_response()
