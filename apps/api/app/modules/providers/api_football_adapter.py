from collections.abc import Mapping
from typing import Any, NoReturn

from app.schemas.providers import (
    ProviderApiFootballReadOnlyAdapterStatus,
    ProviderIdentity,
    ProviderObservation,
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
        _ = query
        assert_api_football_provider_disabled("fetch_fixtures")

    def fetch_results(self, query: Mapping[str, Any] | None = None) -> list[ProviderObservation]:
        _ = query
        assert_api_football_provider_disabled("fetch_results")

    def fetch_team_statistics(self, query: Mapping[str, Any] | None = None) -> list[ProviderObservation]:
        _ = query
        assert_api_football_provider_disabled("fetch_team_statistics")

    def fetch_standings(self, query: Mapping[str, Any] | None = None) -> list[ProviderObservation]:
        _ = query
        assert_api_football_provider_disabled("fetch_standings")

    def fetch_lineups(self, query: Mapping[str, Any] | None = None) -> list[ProviderObservation]:
        _ = query
        assert_api_football_provider_disabled("fetch_lineups")

    def fetch_events(self, query: Mapping[str, Any] | None = None) -> list[ProviderObservation]:
        _ = query
        assert_api_football_provider_disabled("fetch_events")


def get_api_football_read_only_adapter() -> ApiFootballReadOnlyAdapter:
    return ApiFootballReadOnlyAdapter()


def build_api_football_read_only_adapter_status(
    status: ProviderApiFootballReadOnlyAdapterStatus | None = None,
) -> ProviderApiFootballReadOnlyAdapterStatus:
    """Return a blocked status, ignoring caller-provided or constructed unsafe inputs."""
    _ = status
    return ProviderApiFootballReadOnlyAdapterStatus()
