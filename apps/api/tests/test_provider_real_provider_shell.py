from collections.abc import Callable
from datetime import UTC, datetime
import json
import socket

import pytest

from app.modules.providers.contracts import SportsDataProviderProtocol
from app.modules.providers.real_provider_shell import (
    REAL_PROVIDER_SHELL_LABEL,
    ProviderNetworkDisabledError,
    RealProviderAdapterShell,
    assert_provider_network_disabled,
    build_real_provider_shell_status,
)
from app.schemas.providers import (
    ProviderObservation,
    RawPayloadReference,
)


def aware_time(hour: int) -> datetime:
    return datetime(2026, 1, 1, hour, 0, tzinfo=UTC)


def shell_observation() -> ProviderObservation:
    return ProviderObservation(
        provider=REAL_PROVIDER_SHELL_LABEL,
        provider_event_id="PLACEHOLDER_REAL_PROVIDER_SHELL_EVENT",
        observed_at=aware_time(10),
        available_at=aware_time(11),
        fetched_at=aware_time(12),
        source_version="REAL_PROVIDER_SHELL_PLACEHOLDER_v1",
        raw_hash="PLACEHOLDER_REAL_PROVIDER_SHELL_HASH",
        quality_flags=["PLACEHOLDER", "SHELL_ONLY"],
        data={"status": "PLACEHOLDER_ONLY"},
    )


def shell_raw_payload_ref() -> RawPayloadReference:
    return RawPayloadReference(
        provider=REAL_PROVIDER_SHELL_LABEL,
        provider_event_id="PLACEHOLDER_REAL_PROVIDER_SHELL_EVENT",
        fetched_at=aware_time(12),
        source_version="REAL_PROVIDER_SHELL_PLACEHOLDER_v1",
        raw_hash="PLACEHOLDER_REAL_PROVIDER_SHELL_HASH",
    )


def test_real_provider_adapter_shell_satisfies_provider_protocol() -> None:
    assert isinstance(RealProviderAdapterShell(), SportsDataProviderProtocol)


def test_real_provider_adapter_shell_identity_capabilities_and_coverage_are_disabled() -> None:
    adapter = RealProviderAdapterShell()
    identity = adapter.identity()
    health = adapter.health()
    coverage = adapter.coverage()

    assert identity.provider == REAL_PROVIDER_SHELL_LABEL
    assert identity.enabled is False
    assert identity.api_football_connected is False
    assert identity.network_calls_enabled is False
    assert identity.credentials_configured is False
    assert identity.production_mock_fallback_allowed is False
    assert health["provider_enabled"] is False
    assert health["network_calls_enabled"] is False
    assert health["credentials_configured"] is False
    assert health["http_client_enabled"] is False
    assert health["provider_base_url_configured"] is False
    assert health["real_requests_enabled"] is False
    assert health["db_ingestion_enabled"] is False
    assert health["prediction_creation_enabled"] is False
    assert coverage["real_sports_coverage"] is False

    for capability in adapter.capabilities():
        assert capability.enabled is False
        assert capability.status == "disabled"

    for capability in adapter.capability_matrix().as_list():
        assert capability.enabled is False
        assert capability.status == "disabled"


def test_real_provider_adapter_shell_metadata_has_no_url_credentials_or_production_payloads() -> None:
    adapter = RealProviderAdapterShell()
    serialized = json.dumps(
        {
            "identity": adapter.identity().model_dump(),
            "health": adapter.health(),
            "coverage": adapter.coverage(),
            "status": build_real_provider_shell_status().model_dump(),
        },
        default=str,
        sort_keys=True,
    ).lower()

    forbidden_fragments = (
        "https://",
        "http://",
        "api-football.com",
        "api-sports",
        "rapidapi",
        "x-rapidapi",
        "api_key",
        "token",
        "password",
        "provider_credentials",
        "bookmaker",
        "winner",
        "home_score",
        "away_score",
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized


def test_real_provider_shell_status_is_public_safe_and_disabled() -> None:
    status = build_real_provider_shell_status()

    assert status.label == REAL_PROVIDER_SHELL_LABEL
    assert status.status == "blocked_shell_only"
    assert status.provider_enabled is False
    assert status.providers_enabled is False
    assert status.api_football_connected is False
    assert status.network_calls_enabled is False
    assert status.credentials_configured is False
    assert status.http_client_enabled is False
    assert status.provider_base_url_configured is False
    assert status.provider_endpoint_configured is False
    assert status.real_requests_enabled is False
    assert status.db_ingestion_enabled is False
    assert status.prediction_creation_enabled is False
    assert status.production_payloads_enabled is False


@pytest.mark.parametrize(
    "operation",
    [
        lambda adapter: adapter.fetch_competitions(),
        lambda adapter: adapter.fetch_fixtures({"from": aware_time(10)}),
        lambda adapter: adapter.fetch_fixture("PLACEHOLDER_REAL_PROVIDER_SHELL_EVENT"),
        lambda adapter: adapter.fetch_lineups("PLACEHOLDER_REAL_PROVIDER_SHELL_EVENT"),
        lambda adapter: adapter.fetch_injuries({"scope": "PLACEHOLDER_ONLY"}),
        lambda adapter: adapter.fetch_statistics("PLACEHOLDER_REAL_PROVIDER_SHELL_EVENT"),
        lambda adapter: adapter.fetch_live_events("PLACEHOLDER_REAL_PROVIDER_SHELL_EVENT"),
        lambda adapter: adapter.fetch_odds(
            "PLACEHOLDER_REAL_PROVIDER_SHELL_EVENT",
            "PLACEHOLDER_MARKET",
            aware_time(11),
        ),
        lambda adapter: adapter.normalize(shell_raw_payload_ref()),
        lambda adapter: adapter.map_entity(shell_observation()),
        lambda adapter: adapter.temporal_metadata(shell_observation()),
        lambda adapter: adapter.quality_report(shell_observation()),
    ],
)
def test_real_provider_shell_data_producing_methods_are_blocked(
    operation: Callable[[RealProviderAdapterShell], object],
) -> None:
    adapter = RealProviderAdapterShell()

    with pytest.raises(ProviderNetworkDisabledError, match="disabled in Phase 14"):
        operation(adapter)


def test_real_provider_shell_egress_guard_blocks_without_touching_socket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*args: object, **kwargs: object) -> None:
        raise AssertionError("real provider shell egress guard must not touch sockets")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    with pytest.raises(ProviderNetworkDisabledError, match="disabled in Phase 14"):
        assert_provider_network_disabled("test_network_guard")
