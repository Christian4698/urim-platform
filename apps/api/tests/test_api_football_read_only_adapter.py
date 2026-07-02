from collections.abc import Callable
import json
import socket

import pytest

from app.modules.providers.api_football_adapter import (
    API_FOOTBALL_READ_ONLY_ADAPTER_LABEL,
    ApiFootballProviderDisabledError,
    ApiFootballReadOnlyAdapter,
    assert_api_football_provider_disabled,
    build_api_football_read_only_adapter_status,
)
from app.schemas.providers import ProviderApiFootballReadOnlyAdapterStatus


def test_api_football_read_only_adapter_is_disabled_by_default() -> None:
    adapter = ApiFootballReadOnlyAdapter()
    identity = adapter.identity()
    health = adapter.health()
    status = adapter.status()

    assert adapter.enabled is False
    assert adapter.network_calls_enabled is False
    assert adapter.db_ingestion_enabled is False
    assert adapter.prediction_creation_enabled is False
    assert adapter.betting_enabled is False
    assert identity.provider == API_FOOTBALL_READ_ONLY_ADAPTER_LABEL
    assert identity.enabled is False
    assert identity.network_calls_enabled is False
    assert identity.credentials_configured is False
    assert health["enabled"] is False
    assert health["connected"] is False
    assert health["network_calls_enabled"] is False
    assert health["db_ingestion_enabled"] is False
    assert health["credentials_loaded"] is False
    assert health["prediction_creation_enabled"] is False
    assert health["betting_enabled"] is False
    assert status.status == "disabled_until_provider_activation_gate_approved"
    assert status.enabled is False
    assert status.connected is False
    assert status.network_calls_enabled is False
    assert status.db_ingestion_enabled is False
    assert status.credentials_loaded is False
    assert status.prediction_creation_enabled is False
    assert status.betting_enabled is False


@pytest.mark.parametrize(
    "operation",
    [
        lambda adapter: adapter.fetch_fixtures({"scope": "PLACEHOLDER_ONLY"}),
        lambda adapter: adapter.fetch_results({"scope": "PLACEHOLDER_ONLY"}),
        lambda adapter: adapter.fetch_team_statistics({"scope": "PLACEHOLDER_ONLY"}),
        lambda adapter: adapter.fetch_standings({"scope": "PLACEHOLDER_ONLY"}),
        lambda adapter: adapter.fetch_lineups({"scope": "PLACEHOLDER_ONLY"}),
        lambda adapter: adapter.fetch_events({"scope": "PLACEHOLDER_ONLY"}),
    ],
)
def test_api_football_read_only_adapter_methods_refuse_execution(
    operation: Callable[[ApiFootballReadOnlyAdapter], object],
) -> None:
    adapter = ApiFootballReadOnlyAdapter()

    with pytest.raises(ApiFootballProviderDisabledError, match="disabled until provider activation gate"):
        operation(adapter)


def test_api_football_read_only_guard_blocks_without_touching_socket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*args: object, **kwargs: object) -> None:
        raise AssertionError("API-Football read-only adapter guard must not touch sockets")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    with pytest.raises(ApiFootballProviderDisabledError, match="disabled until provider activation gate"):
        assert_api_football_provider_disabled("test_network_guard")


def test_api_football_read_only_adapter_public_serialization_is_safe() -> None:
    adapter = ApiFootballReadOnlyAdapter()
    serialized = json.dumps(
        {
            "identity": adapter.identity().model_dump(),
            "health": adapter.health(),
            "status": adapter.status().model_dump(),
        },
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
        "real_requests_enabled",
        "provider_base_url_configured",
        "provider_endpoint_configured",
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized


def test_api_football_read_only_status_refuses_constructed_dangerous_inputs() -> None:
    unsafe_status = ProviderApiFootballReadOnlyAdapterStatus.model_construct(
        enabled=True,
        connected=True,
        network_calls_enabled=True,
        db_ingestion_enabled=True,
        credentials_loaded=True,
        prediction_creation_enabled=True,
        betting_enabled=True,
        status="enabled",
    )

    status = build_api_football_read_only_adapter_status(status=unsafe_status)

    assert status.status == "disabled_until_provider_activation_gate_approved"
    assert status.enabled is False
    assert status.connected is False
    assert status.network_calls_enabled is False
    assert status.db_ingestion_enabled is False
    assert status.credentials_loaded is False
    assert status.prediction_creation_enabled is False
    assert status.betting_enabled is False
