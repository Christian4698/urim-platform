from collections.abc import Mapping
from typing import Any, NoReturn

from app.modules.providers.api_football_transport import (
    ApiFootballTestTransport,
    ApiFootballTransportProtocol,
    ApiFootballTransportResponse,
)
from app.schemas.providers import (
    ProviderApiFootballReadOnlyAdapterStatus,
    ProviderIdentity,
    ProviderObservation,
    RawPayloadReference,
)

API_FOOTBALL_READ_ONLY_ADAPTER_LABEL = "api_football_read_only_adapter"


class ApiFootballProviderDisabledError(RuntimeError):
    """Raised before any API-Football read-only operation can execute."""


def assert_api_football_provider_disabled(operation: str) -> NoReturn:
    """Block API-Football access before sockets, clients, credentials or storage are touched."""
    raise ApiFootballProviderDisabledError(
        "API-Football read-only adapter is disabled until provider activation gate approval "
        f"for operation: {operation}"
    )


class ApiFootballReadOnlyAdapter:
    """Blocked read-only adapter shape for future API-Football integration."""

    enabled = False
    network_calls_enabled = False
    db_ingestion_enabled = False
    prediction_creation_enabled = False
    betting_enabled = False

    def __init__(
        self,
        transport: ApiFootballTransportProtocol | None = None,
        allow_test_transport: bool = False,
    ) -> None:
        self._transport = transport
        self._allow_test_transport = allow_test_transport

    def identity(self) -> ProviderIdentity:
        return ProviderIdentity(
            provider=API_FOOTBALL_READ_ONLY_ADAPTER_LABEL,
            display_name="API-Football read-only adapter",
        )

    def status(self) -> ProviderApiFootballReadOnlyAdapterStatus:
        return build_api_football_read_only_adapter_status()

    def health(self) -> dict[str, Any]:
        return {
            "label": API_FOOTBALL_READ_ONLY_ADAPTER_LABEL,
            "status": "disabled_until_provider_activation_gate_approved",
            "enabled": False,
            "connected": False,
            "network_calls_enabled": False,
            "db_ingestion_enabled": False,
            "credentials_loaded": False,
            "prediction_creation_enabled": False,
            "betting_enabled": False,
        }

    def fetch_fixtures(self, query: Mapping[str, Any] | None = None) -> list[ProviderObservation]:
        transport = self._require_test_transport("fetch_fixtures")
        return [self._observation_from_response(transport.fetch_fixtures(query))]

    def fetch_results(self, query: Mapping[str, Any] | None = None) -> list[ProviderObservation]:
        transport = self._require_test_transport("fetch_results")
        return [self._observation_from_response(transport.fetch_results(query))]

    def fetch_team_statistics(self, query: Mapping[str, Any] | None = None) -> list[ProviderObservation]:
        transport = self._require_test_transport("fetch_team_statistics")
        return [self._observation_from_response(transport.fetch_team_statistics(query))]

    def fetch_standings(self, query: Mapping[str, Any] | None = None) -> list[ProviderObservation]:
        transport = self._require_test_transport("fetch_standings")
        return [self._observation_from_response(transport.fetch_standings(query))]

    def fetch_lineups(self, query: Mapping[str, Any] | None = None) -> list[ProviderObservation]:
        transport = self._require_test_transport("fetch_lineups")
        return [self._observation_from_response(transport.fetch_lineups(query))]

    def fetch_events(self, query: Mapping[str, Any] | None = None) -> list[ProviderObservation]:
        transport = self._require_test_transport("fetch_events")
        return [self._observation_from_response(transport.fetch_events(query))]

    def _require_test_transport(self, operation: str) -> ApiFootballTransportProtocol:
        if not self._allow_test_transport or not isinstance(self._transport, ApiFootballTestTransport):
            assert_api_football_provider_disabled(operation)
        return self._transport

    def _observation_from_response(self, response: ApiFootballTransportResponse) -> ProviderObservation:
        raw_payload_ref = RawPayloadReference(
            provider=response.provider_name,
            provider_event_id=response.provider_event_id,
            fetched_at=response.fetched_at,
            source_version=response.source_version,
            raw_hash=response.raw_hash,
            metadata={
                "payload_marker": response.payload_marker,
                "environment_marker": response.environment_marker,
                "payload_location": "in_memory_api_football_test_transport",
                "response_kind": response.response_kind,
            },
        )
        return ProviderObservation(
            provider=response.provider_name,
            provider_event_id=response.provider_event_id,
            observed_at=response.observed_at,
            available_at=response.available_at,
            fetched_at=response.fetched_at,
            source_version=response.source_version,
            raw_hash=response.raw_hash,
            quality_flags=list(response.quality_flags),
            raw_payload_ref=raw_payload_ref,
            data=response.model_dump(mode="json"),
        )


def get_api_football_read_only_adapter() -> ApiFootballReadOnlyAdapter:
    return ApiFootballReadOnlyAdapter()


def build_api_football_read_only_adapter_status(
    status: ProviderApiFootballReadOnlyAdapterStatus | None = None,
) -> ProviderApiFootballReadOnlyAdapterStatus:
    """Return a blocked status, ignoring caller-provided or constructed unsafe inputs."""
    _ = status
    return ProviderApiFootballReadOnlyAdapterStatus()
