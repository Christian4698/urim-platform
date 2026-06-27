from fastapi import APIRouter

from app.schemas.common import SkeletonCollectionResponse, empty_collection

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=SkeletonCollectionResponse)
def list_tickets() -> SkeletonCollectionResponse:
    return empty_collection(
        "tickets",
        [
            "Bet Center tickets are virtual/internal only.",
            "No real stake is created or executed.",
            "User-declared ticket results are never a learning source for Post-Match Learning.",
        ],
    )
