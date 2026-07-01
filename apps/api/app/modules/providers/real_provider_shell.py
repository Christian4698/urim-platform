from datetime import datetime
from typing import Any, NoReturn

from app.schemas.providers import (
    CanonicalEntityMapping,
    DataQualityReport,
    ProviderCapability,
    ProviderCapabilityMatrix,
    ProviderIdentity,
    ProviderObservation,
    ProviderRealProviderShellStatus,
    RawPayloadReference,
    TemporalAvailabilityMetadata,
    disabled_provider_capabilities,
)

REAL_PROVIDER_SHELL_LABEL = "api_football_future_provider_shell"


class ProviderNetworkDisabledError(RuntimeError):
    """Raised before any future real-provider network path can execute."""


def assert_provider_network_disabled(operation: str) -> NoReturn:
    """Block provider egress in Phase 14 without touching sockets or HTTP clients."""
    raise ProviderNetworkDisabledError(
        f"Provider network access is disabled in Phase 14 for operation: {operation}"
    )


class RealProviderAdapterShell:
    """Blocked shell for a future real provider adapter; not a connector."""

    def identity(self) -> ProviderIdentity:
        return ProviderIdentity(
            provider=REAL_PROVIDER_SHELL_LABEL,
            display_name="API-Football future provider shell",
        )

    def health(self) -> dict[str, Any]:
        return {
            "status": "blocked_shell_only",
            "label": REAL_PROVIDER_SHELL_LABEL,
            "provider_enabled": False,
            "network_calls_enabled": False,
            "credentials_configured": False,
            "http_client_enabled": False,
            "provider_base_url_configured": False,
            "real_requests_enabled": False,
            "db_ingestion_enabled": False,
            "prediction_creation_enabled": False,
        }

    def capabilities(self) -> list[ProviderCapability]:
        return disabled_provider_capabilities()

    def capability_matrix(self) -> ProviderCapabilityMatrix:
        return ProviderCapabilityMatrix()

    def coverage(self) -> dict[str, Any]:
        return {
            "label": REAL_PROVIDER_SHELL_LABEL,
            "coverage_status": "blocked_shell_only",
            "real_sports_coverage": False,
            "provider_enabled": False,
            "network_calls_enabled": False,
        }

    def fetch_competitions(self) -> list[ProviderObservation]:
        assert_provider_network_disabled("fetch_competitions")

    def fetch_fixtures(self, window: dict[str, datetime]) -> list[ProviderObservation]:
        _ = window
        assert_provider_network_disabled("fetch_fixtures")

    def fetch_fixture(self, fixture_id: str) -> ProviderObservation:
        _ = fixture_id
        assert_provider_network_disabled("fetch_fixture")

    def fetch_lineups(self, fixture_id: str) -> list[ProviderObservation]:
        _ = fixture_id
        assert_provider_network_disabled("fetch_lineups")

    def fetch_injuries(self, scope: dict[str, Any]) -> list[ProviderObservation]:
        _ = scope
        assert_provider_network_disabled("fetch_injuries")

    def fetch_statistics(self, fixture_id: str) -> list[ProviderObservation]:
        _ = fixture_id
        assert_provider_network_disabled("fetch_statistics")

    def fetch_live_events(self, fixture_id: str, cursor: str | None = None) -> list[ProviderObservation]:
        _ = (fixture_id, cursor)
        assert_provider_network_disabled("fetch_live_events")

    def fetch_odds(self, event_id: str, market: str, as_of: datetime) -> list[ProviderObservation]:
        _ = (event_id, market, as_of)
        assert_provider_network_disabled("fetch_odds")

    def normalize(self, raw_payload: RawPayloadReference) -> ProviderObservation:
        _ = raw_payload
        assert_provider_network_disabled("normalize")

    def map_entity(self, observation: ProviderObservation) -> CanonicalEntityMapping:
        _ = observation
        assert_provider_network_disabled("map_entity")

    def temporal_metadata(self, observation: ProviderObservation) -> TemporalAvailabilityMetadata:
        _ = observation
        assert_provider_network_disabled("temporal_metadata")

    def quality_report(self, observation: ProviderObservation) -> DataQualityReport:
        _ = observation
        assert_provider_network_disabled("quality_report")


def get_real_provider_adapter_shell() -> RealProviderAdapterShell:
    return RealProviderAdapterShell()


def build_real_provider_shell_status() -> ProviderRealProviderShellStatus:
    return ProviderRealProviderShellStatus()
