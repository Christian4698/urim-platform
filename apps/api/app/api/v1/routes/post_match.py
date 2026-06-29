from fastapi import APIRouter

from app.schemas.common import SkeletonCollectionResponse, empty_collection

router = APIRouter(prefix="/post-match", tags=["post-match"])


@router.get("/outcomes", response_model=SkeletonCollectionResponse)
def list_post_match_outcomes() -> SkeletonCollectionResponse:
    return empty_collection(
        "post_match_outcomes",
        [
            "No production sports outcomes are fabricated in Phase 8.",
            "Future Post-Match Learning must learn only from verified post_match_outcomes.",
        ],
    )
