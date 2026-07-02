import json
import socket
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.providers.api_football_smoke_client import (
    API_FOOTBALL_SMOKE_ENV_NAMES,
    ApiFootballSmokeDisabledError,
)
from app.modules.providers.api_football_smoke_runner import (
    MANUAL_SMOKE_COMPLETED_STATUS,
    MANUAL_SMOKE_DISABLED_STATUS,
    MANUAL_SMOKE_MODE,
    MANUAL_SMOKE_PROVIDER,
    MANUAL_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS,
    ManualApiFootballSmokeRunResult,
    assert_manual_api_football_smoke_output_safe,
    main,
    run_manual_api_football_smoke_check,
)
from app.modules.providers.api_football_transport import stable_raw_hash

client = TestClient(app)

FAKE_RUNNER_AUTH = "DEMO_NON_PROD_FAKE_PHASE19_AUTH_MATERIAL"
FAKE_RUNNER_BASE_URL = "https://example.invalid/phase19-manual-smoke"


class RecordingSmokeTransport:
    def __init__(self, payload: Mapping[str, Any] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.payload = dict(
            payload
            or {
                "marker": "DEMO_NON_PROD",
                "status": "PLACEHOLDER_MANUAL_SMOKE_OK",
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


def fake_runner_environ(**overrides: str) -> dict[str, str]:
    environ = {
        API_FOOTBALL_SMOKE_ENV_NAMES[0]: "true",
        API_FOOTBALL_SMOKE_ENV_NAMES[1]: FAKE_RUNNER_AUTH,
        API_FOOTBALL_SMOKE_ENV_NAMES[2]: FAKE_RUNNER_BASE_URL,
        API_FOOTBALL_SMOKE_ENV_NAMES[3]: "true",
        API_FOOTBALL_SMOKE_ENV_NAMES[4]: "true",
        "APP_ENV": "development",
    }
    environ.update(overrides)
    return environ


def assert_result_has_no_manual_smoke_leaks(result: ManualApiFootballSmokeRunResult) -> None:
    serialized = json.dumps(result.public_safe_summary(), sort_keys=True).lower()
    assert FAKE_RUNNER_AUTH.lower() not in serialized
    assert FAKE_RUNNER_BASE_URL.lower() not in serialized
    for env_name in API_FOOTBALL_SMOKE_ENV_NAMES:
        assert env_name.lower() not in serialized


def test_manual_smoke_runner_disabled_by_default() -> None:
    result = run_manual_api_football_smoke_check(environ={})

    assert result == ManualApiFootballSmokeRunResult()
    assert result.status == MANUAL_SMOKE_DISABLED_STATUS
    assert result.executed is False
    assert result.provider == MANUAL_SMOKE_PROVIDER
    assert result.mode == MANUAL_SMOKE_MODE
    assert result.db_writes is False
    assert result.prediction_created is False
    assert result.betting_created is False
    assert result.payload_hash is None


def test_manual_smoke_runner_refuses_before_socket_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_create_connection(*args: object, **kwargs: object) -> None:
        raise AssertionError("manual API-Football smoke runner must not open sockets by default")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    result = run_manual_api_football_smoke_check(environ={})

    assert result.executed is False
    assert result.status == MANUAL_SMOKE_DISABLED_STATUS


def test_manual_smoke_runner_refuses_without_explicit_activation() -> None:
    transport = RecordingSmokeTransport()

    result = run_manual_api_football_smoke_check(transport=transport, environ={})

    assert result.executed is False
    assert result.status == MANUAL_SMOKE_DISABLED_STATUS
    assert transport.calls == []


def test_manual_smoke_runner_refuses_without_injected_transport() -> None:
    result = run_manual_api_football_smoke_check(environ=fake_runner_environ())

    assert result.executed is False
    assert result.status == MANUAL_SMOKE_DISABLED_STATUS


def test_manual_smoke_runner_refuses_production_environment() -> None:
    transport = RecordingSmokeTransport()

    result = run_manual_api_football_smoke_check(
        transport=transport,
        environ=fake_runner_environ(APP_ENV="production"),
    )

    assert result.executed is False
    assert result.status == MANUAL_SMOKE_DISABLED_STATUS
    assert transport.calls == []


def test_manual_smoke_runner_success_requires_mocked_injected_transport() -> None:
    payload = {
        "marker": "DEMO_NON_PROD",
        "status": "PLACEHOLDER_MANUAL_SMOKE_OK",
        "payload_state": "NO_PUBLIC_PROVIDER_DATA",
    }
    transport = RecordingSmokeTransport(payload)

    result = run_manual_api_football_smoke_check(
        transport=transport,
        environ=fake_runner_environ(),
        query={"scope": "phase19_manual_smoke_runner"},
    )

    assert transport.calls == [
        {
            "base_url": FAKE_RUNNER_BASE_URL,
            "auth_material": FAKE_RUNNER_AUTH,
            "query": {"scope": "phase19_manual_smoke_runner"},
        }
    ]
    assert result.status == MANUAL_SMOKE_COMPLETED_STATUS
    assert result.executed is True
    assert result.db_writes is False
    assert result.prediction_created is False
    assert result.betting_created is False
    assert result.payload_hash == stable_raw_hash({"smoke_payload": payload})
    assert_result_has_no_manual_smoke_leaks(result)


def test_manual_smoke_runner_refuses_unsafe_transport_output() -> None:
    for payload in (
        {"status": "PLACEHOLDER", "echo": FAKE_RUNNER_AUTH},
        {"status": "PLACEHOLDER", "echo": FAKE_RUNNER_BASE_URL},
        {"status": "PLACEHOLDER", "credential": "DEMO_NON_PROD_FAKE_CREDENTIAL"},
    ):
        result = run_manual_api_football_smoke_check(
            transport=RecordingSmokeTransport(payload),
            environ=fake_runner_environ(),
        )

        assert result.executed is False
        assert result.status == MANUAL_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS
        assert result.payload_hash is None
        assert_result_has_no_manual_smoke_leaks(result)


def test_manual_smoke_runner_output_validator_rejects_constructed_leaks() -> None:
    unsafe_result = ManualApiFootballSmokeRunResult(
        status=FAKE_RUNNER_AUTH,
        executed=True,
        payload_hash="placeholder_hash",
    )

    with pytest.raises(ApiFootballSmokeDisabledError, match="non-public provider material"):
        assert_manual_api_football_smoke_output_safe(
            unsafe_result,
            environ=fake_runner_environ(),
        )


def test_manual_smoke_runner_main_prints_safe_disabled_result(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    serialized = captured.out.lower()

    assert exit_code == 0
    assert payload["status"] == MANUAL_SMOKE_DISABLED_STATUS
    assert payload["executed"] is False
    assert payload["provider"] == MANUAL_SMOKE_PROVIDER
    assert payload["mode"] == MANUAL_SMOKE_MODE
    assert payload["db_writes"] is False
    assert payload["prediction_created"] is False
    assert payload["betting_created"] is False
    for env_name in API_FOOTBALL_SMOKE_ENV_NAMES:
        assert env_name.lower() not in serialized


def test_manual_smoke_runner_is_not_imported_by_fastapi_routes() -> None:
    api_sources = [
        *Path("app/api").rglob("*.py"),
        Path("app/main.py"),
    ]

    for source_path in api_sources:
        assert "api_football_smoke_runner" not in source_path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/providers/smoke",
        "/api/v1/providers/smoke/run",
        "/api/v1/providers/manual-smoke",
        "/api/v1/providers/api-football/manual-smoke",
    ],
)
def test_manual_smoke_runner_has_no_public_endpoint(path: str) -> None:
    response = client.get(path)

    assert response.status_code == 404
