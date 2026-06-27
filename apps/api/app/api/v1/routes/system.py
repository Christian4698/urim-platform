from fastapi import APIRouter

from app.schemas.common import build_metadata
from app.schemas.system import CapabilitiesResponse, disabled_capabilities

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/capabilities", response_model=CapabilitiesResponse)
def capabilities() -> CapabilitiesResponse:
    return CapabilitiesResponse(
        metadata=build_metadata(),
        capabilities=disabled_capabilities(),
        safeguards=[
            "Bet Center is virtual/internal only.",
            "Providers, bookmakers, ML, live and real betting are disabled.",
            "Post-Match Learning may use only verified post_match_outcomes in a future phase.",
        ],
    )
