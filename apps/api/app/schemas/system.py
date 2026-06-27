from pydantic import BaseModel, ConfigDict

from app.core.constants import VIRTUAL_INTERNAL
from app.schemas.common import ApiMetadata


class CapabilityStatus(BaseModel):
    providers_enabled: bool
    api_football_connected: bool
    bookmakers_enabled: bool
    ml_enabled: bool
    live_enabled: bool
    real_betting_enabled: bool
    bet_center_mode: str
    prediction_creation_enabled: bool
    production_mocks_enabled: bool
    production_seed_enabled: bool
    post_match_learning_source: str

    model_config = ConfigDict(extra="forbid")


class CapabilitiesResponse(BaseModel):
    metadata: ApiMetadata
    capabilities: CapabilityStatus
    safeguards: list[str]

    model_config = ConfigDict(extra="forbid")


def disabled_capabilities() -> CapabilityStatus:
    return CapabilityStatus(
        providers_enabled=False,
        api_football_connected=False,
        bookmakers_enabled=False,
        ml_enabled=False,
        live_enabled=False,
        real_betting_enabled=False,
        bet_center_mode=VIRTUAL_INTERNAL,
        prediction_creation_enabled=False,
        production_mocks_enabled=False,
        production_seed_enabled=False,
        post_match_learning_source="post_match_outcomes_only",
    )
