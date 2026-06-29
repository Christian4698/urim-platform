from fastapi import APIRouter

from app.schemas.common import SkeletonCollectionResponse, empty_collection

router = APIRouter(prefix="/fixtures", tags=["fixtures"])


@router.get("", response_model=SkeletonCollectionResponse)
def list_fixtures() -> SkeletonCollectionResponse:
    return empty_collection(
        "fixtures",
        [
            "No provider connector is enabled in Phase 8.",
            "No real fixtures or production sports data are fabricated.",
        ],
    )
