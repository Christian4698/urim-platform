import json
import socket
from collections.abc import Mapping
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.modules.providers.api_football_smoke_client as smoke_module
from app.main import app
from app.modules.providers.api_football_smoke_client import (
    API_FOOTBALL_SMOKE_ENV_NAMES,
    ApiFootballSmokeClient,
    ApiFootballSmokeDisabledError,
    ApiFootballSmokeHttpTransport,
    ApiFootballSmokeTransportProtocol,
    build_api_football_smoke_client_status,
    load_api_football_smoke_config,
)
from app.modules.providers.api_football_transport import stable_raw_hash
from app.schemas.providers import ProviderApiFootballSmokeClientStatus

client = TestClient(app)

FAKE_SMOKE_AUTH = "DEMO_NON_PROD_FAKE_PHASE18_AUTH_MATERIAL"
FAKE_SMOKE_BASE_URL = "https://example.invalid/phase18-smoke"


class RecordingSmokeTransport:
    def __init__(self, payload: Mapping[str, Any] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.payload = dict(
            payload
            or {
                "marker": "DEMO_NON_PROD",
                "status": "PLACEHOLDER_SMOKE_OK",
                "payload_state": "NO_PUBLIC_PROVIDER_DATA",
            }
        )

    def smoke_request(
        self,
        *,
        base_url: str,
        auth_material: str,
        query: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        self.calls.append(
            {
                "base_url": base_url,
                "auth_material": auth_material,
                "query": dict(query or {}),
            }
        )
        return self.payload


def fake_smoke_environ(**overrides: str) -> dict[str, str]:
    environ = {
        API_FOOTBALL_SMOKE_ENV_NAMES[0]: "true",
        API_FOOTBALL_SMOKE_ENV_NAMES[1]: FAKE_SMOKE_AUTH,
        API_FOOTBALL_SMOKE_ENV_NAMES[2]: FAKE_SMOKE_BASE_URL,
        API_FOOTBALL_SMOKE_ENV_NAMES[3]: "true",
        API_FOOTBALL_SMOKE_ENV_NAMES[4]: "true",
        "APP_ENV": "development",
    }
    environ.update(overrides)
    return environ


def test_api_football_smoke_client_disabled_by_default() -> None:
    config = load_api_football_smoke_config({})
    client_under_test = ApiFootballSmokeClient(environ={})

    assert config.smoke_mode_enabled is False
    assert config.auth_material_present is False
    assert config.base_url_present is False
    assert config.read_only_confirmed is False
    assert config.non_production_confirmed is False
    assert client_under_test.enabled_by_default is False
    assert client_under_test.network_calls_enabled_by_default is False
    assert client_under_test.db_ingestion_enabled is False
    assert client_under_test.prediction_creation_enabled is False
    assert client_under_test.betting_enabled is False

    with pytest.raises(ApiFootballSmokeDisabledError, match="smoke_mode_not_explicitly_enabled"):
        client_under_test.run_smoke_check()


def test_api_football_smoke_client_refuses_before_socket_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_create_connection(*args: object, **kwargs: object) -> None:
        raise AssertionError("API-Football smoke client must not open sockets by default")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    with pytest.raises(ApiFootballSmokeDisabledError):
        ApiFootballSmokeClient(environ={}).run_smoke_check()


def test_api_football_smoke_client_requires_injected_transport_with_fake_env() -> None:
    with pytest.raises(ApiFootballSmokeDisabledError, match="transport_explicitly_injected_required"):
        ApiFootballSmokeClient(environ=fake_smoke_environ()).run_smoke_check()


def test_api_football_smoke_client_refuses_production_even_with_fake_env() -> None:
    transport = RecordingSmokeTransport()

    with pytest.raises(ApiFootballSmokeDisabledError, match="production_environment_refused"):
        ApiFootballSmokeClient(
            transport=transport,
            environ=fake_smoke_environ(APP_ENV="production"),
        ).run_smoke_check()

    assert transport.calls == []


def test_api_football_smoke_client_runs_only_with_injected_transport_and_redacts_result() -> None:
    payload = {
        "marker": "DEMO_NON_PROD",
        "status": "PLACEHOLDER_SMOKE_OK",
        "payload_state": "NO_PUBLIC_PROVIDER_DATA",
    }
    transport = RecordingSmokeTransport(payload)
    client_under_test = ApiFootballSmokeClient(
        transport=transport,
        environ=fake_smoke_environ(),
    )

    assert isinstance(transport, ApiFootballSmokeTransportProtocol)
    result = client_under_test.run_smoke_check(query={"scope": "phase18_smoke_contract"})
    summary = result.public_safe_summary()
    serialized = json.dumps(summary, sort_keys=True).lower()

    assert transport.calls == [
        {
            "base_url": FAKE_SMOKE_BASE_URL,
            "auth_material": FAKE_SMOKE_AUTH,
            "query": {"scope": "phase18_smoke_contract"},
        }
    ]
    assert result.provider_gate_consulted is True
    assert result.provider_gate_decision == "blocked"
    assert result.read_only is True
    assert result.payload_hash == stable_raw_hash({"smoke_payload": payload})
    assert result.payload_top_level_keys == ("marker", "payload_state", "status")
    assert result.db_ingestion_enabled is False
    assert result.prediction_creation_enabled is False
    assert result.betting_enabled is False
    assert result.credentials_exposed is False
    assert FAKE_SMOKE_AUTH.lower() not in serialized
    assert FAKE_SMOKE_BASE_URL.lower() not in serialized
    for env_name in API_FOOTBALL_SMOKE_ENV_NAMES:
        assert env_name.lower() not in serialized


def test_api_football_smoke_client_blocks_payloads_that_echo_secret_or_url() -> None:
    for payload in (
        {"status": "PLACEHOLDER", "echo": FAKE_SMOKE_AUTH},
        {"status": "PLACEHOLDER", "echo": FAKE_SMOKE_BASE_URL},
        {"status": "PLACEHOLDER", "token": "DEMO_NON_PROD_FAKE_TOKEN"},
    ):
        with pytest.raises(ApiFootballSmokeDisabledError, match="non-public provider material"):
            ApiFootballSmokeClient(
                transport=RecordingSmokeTransport(payload),
                environ=fake_smoke_environ(),
            ).run_smoke_check()


def test_api_football_smoke_http_transport_requires_explicit_callable(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_create_connection(*args: object, **kwargs: object) -> None:
        raise AssertionError("API-Football smoke HTTP transport must not open sockets without injection")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)
    transport = ApiFootballSmokeHttpTransport()

    assert transport.network_calls_enabled_by_default is False
    assert transport.db_ingestion_enabled is False
    assert transport.prediction_creation_enabled is False
    assert transport.betting_enabled is False
    with pytest.raises(ApiFootballSmokeDisabledError, match="explicit local injection"):
        ApiFootballSmokeClient(
            transport=transport,
            environ=fake_smoke_environ(),
        ).run_smoke_check()


def test_api_football_smoke_status_is_public_safe_even_with_fake_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for env_name, env_value in fake_smoke_environ().items():
        monkeypatch.setenv(env_name, env_value)

    response = client.get("/api/v1/providers/readiness")
    payload = response.json()
    status = payload["api_football_smoke_client_status"]
    serialized = response.text.lower()

    assert response.status_code == 200
    assert status == build_api_football_smoke_client_status().model_dump(mode="json")
    assert status["status"] == "disabled_until_explicit_local_smoke_env"
    assert status["enabled_by_default"] is False
    assert status["smoke_mode_enabled"] is False
    assert status["network_calls_enabled_by_default"] is False
    assert status["public_endpoint_enabled"] is False
    assert status["db_ingestion_enabled"] is False
    assert status["credentials_exposed"] is False
    assert status["prediction_creation_enabled"] is False
    assert status["betting_enabled"] is False
    assert status["real_provider_connected"] is False
    assert FAKE_SMOKE_AUTH.lower() not in serialized
    assert FAKE_SMOKE_BASE_URL.lower() not in serialized
    for env_name in API_FOOTBALL_SMOKE_ENV_NAMES:
        assert env_name.lower() not in serialized


def test_api_football_smoke_status_refuses_constructed_dangerous_inputs() -> None:
    unsafe_status = ProviderApiFootballSmokeClientStatus.model_construct(
        enabled_by_default=True,
        smoke_mode_enabled=True,
        network_calls_enabled_by_default=True,
        public_endpoint_enabled=True,
        db_ingestion_enabled=True,
        credentials_exposed=True,
        prediction_creation_enabled=True,
        betting_enabled=True,
        real_provider_connected=True,
        status="enabled",
    )

    status = build_api_football_smoke_client_status(status=unsafe_status)

    assert status.enabled_by_default is False
    assert status.smoke_mode_enabled is False
    assert status.network_calls_enabled_by_default is False
    assert status.public_endpoint_enabled is False
    assert status.db_ingestion_enabled is False
    assert status.credentials_exposed is False
    assert status.prediction_creation_enabled is False
    assert status.betting_enabled is False
    assert status.real_provider_connected is False
    assert status.status == "disabled_until_explicit_local_smoke_env"


def test_api_football_smoke_module_does_not_import_provider_http_clients() -> None:
    source = smoke_module.__loader__.get_source(smoke_module.__name__) or ""
    lowered_source = source.lower()

    for forbidden_import in ("import requests", "import httpx", "import aiohttp", "socket.create_connection"):
        assert forbidden_import not in lowered_source
