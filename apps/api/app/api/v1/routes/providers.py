from fastapi import APIRouter

from app.schemas.common import SkeletonCollectionResponse, empty_collection

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=SkeletonCollectionResponse)
def list_providers() -> SkeletonCollectionResponse:
    return empty_collection(
        "providers",
        [
            "Provider connectors are disabled in Phase 3.",
            "API-Football is not connected.",
            "No bookmaker integration is exposed.",
        ],
    )
