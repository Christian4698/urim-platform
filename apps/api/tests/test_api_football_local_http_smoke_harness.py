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
from app.modules.providers.api_football_transport import stable_raw_hash
from scripts.api_football_local_smoke_harness import (
    LOCAL_HTTP_SMOKE_COMPLETED_STATUS,
    LOCAL_HTTP_SMOKE_DISABLED_STATUS,
    LOCAL_HTTP_SMOKE_MODE,
    LOCAL_HTTP_SMOKE_PROVIDER,
    LOCAL_HTTP_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS,
    LocalApiFootballHttpSmokeHarnessResult,
    assert_local_api_football_http_smoke_harness_output_safe,
    main,
    run_local_api_football_http_smoke_harness,
)

client = TestClient(app)

FAKE_HARNESS_AUTH = "DEMO_NON_PROD_FAKE_PHASE21_AUTH_MATERIAL"
FAKE_HARNESS_BASE_URL = "https://example.invalid/phase21-local-http-smoke"


class RecordingRequestCallable:
    def __init__(self, payload: Mapping[str, Any] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.payload = dict(
            payload
            or {
                "marker": "DEMO_NON_PROD",
                "status": "PLACEHOLDER_LOCAL_HTTP_SMOKE_OK",
                "payload_state": "NO_PUBLIC_PROVIDER_DATA",
            }
        )

    def __call__(
        self,
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


def fake_harness_environ(**overrides: str) -> dict[str, str]:
    environ = {
        API_FOOTBALL_SMOKE_ENV_NAMES[0]: "true",
        API_FOOTBALL_SMOKE_ENV_NAMES[1]: FAKE_HARNESS_AUTH,
        API_FOOTBALL_SMOKE_ENV_NAMES[2]: FAKE_HARNESS_BASE_URL,
        API_FOOTBALL_SMOKE_ENV_NAMES[3]: "true",
        API_FOOTBALL_SMOKE_ENV_NAMES[4]: "true",
        "APP_ENV": "development",
    }
    environ.update(overrides)
    return environ


def assert_result_has_no_local_http_smoke_leaks(result: LocalApiFootballHttpSmokeHarnessResult) -> None:
    serialized = json.dumps(result.public_safe_summary(), sort_keys=True).lower()
    assert FAKE_HARNESS_AUTH.lower() not in serialized
    assert FAKE_HARNESS_BASE_URL.lower() not in serialized
    for env_name in API_FOOTBALL_SMOKE_ENV_NAMES:
        assert env_name.lower() not in serialized
    for fragment in ("api_key", "credential", "password", "secret", "token", "http://", "https://"):
        assert fragment not in serialized


def test_local_http_smoke_harness_disabled_by_default() -> None:
    result = run_local_api_football_http_smoke_harness(environ={})

    assert result == LocalApiFootballHttpSmokeHarnessResult()
    assert result.status == LOCAL_HTTP_SMOKE_DISABLED_STATUS
    assert result.executed is False
    assert result.provider == LOCAL_HTTP_SMOKE_PROVIDER
    assert result.mode == LOCAL_HTTP_SMOKE_MODE
    assert result.db_writes is False
    assert result.prediction_created is False
    assert result.betting_created is False
    assert result.payload_hash is None


def test_local_http_smoke_harness_refuses_before_socket_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_create_connection(*args: object, **kwargs: object) -> None:
        raise AssertionError("local HTTP smoke harness must not open sockets by default")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    result = run_local_api_football_http_smoke_harness(environ={})

    assert result.executed is False
    assert result.status == LOCAL_HTTP_SMOKE_DISABLED_STATUS


def test_local_http_smoke_harness_refuses_without_explicit_activation() -> None:
    request_callable = RecordingRequestCallable()

    result = run_local_api_football_http_smoke_harness(
        request_callable=request_callable,
        environ={},
    )

    assert result.executed is False
    assert result.status == LOCAL_HTTP_SMOKE_DISABLED_STATUS
    assert request_callable.calls == []


def test_local_http_smoke_harness_refuses_without_request_callable() -> None:
    result = run_local_api_football_http_smoke_harness(environ=fake_harness_environ())

    assert result.executed is False
    assert result.status == LOCAL_HTTP_SMOKE_DISABLED_STATUS


def test_local_http_smoke_harness_refuses_production_environment() -> None:
    request_callable = RecordingRequestCallable()

    result = run_local_api_football_http_smoke_harness(
        request_callable=request_callable,
        environ=fake_harness_environ(APP_ENV="production"),
    )

    assert result.executed is False
    assert result.status == LOCAL_HTTP_SMOKE_DISABLED_STATUS
    assert request_callable.calls == []


def test_local_http_smoke_harness_success_requires_mocked_request_callable() -> None:
    payload = {
        "marker": "DEMO_NON_PROD",
        "status": "PLACEHOLDER_LOCAL_HTTP_SMOKE_OK",
        "payload_state": "NO_PUBLIC_PROVIDER_DATA",
    }
    request_callable = RecordingRequestCallable(payload)

    result = run_local_api_football_http_smoke_harness(
        request_callable=request_callable,
        environ=fake_harness_environ(),
        query={"scope": "phase21_local_http_smoke_harness"},
    )

    assert request_callable.calls == [
        {
            "base_url": FAKE_HARNESS_BASE_URL,
            "auth_material": FAKE_HARNESS_AUTH,
            "query": {"scope": "phase21_local_http_smoke_harness"},
        }
    ]
    assert result.status == LOCAL_HTTP_SMOKE_COMPLETED_STATUS
    assert result.executed is True
    assert result.db_writes is False
    assert result.prediction_created is False
    assert result.betting_created is False
    assert result.payload_hash == stable_raw_hash({"smoke_payload": payload})
    assert_result_has_no_local_http_smoke_leaks(result)


def test_local_http_smoke_harness_refuses_unsafe_request_callable_output() -> None:
    for payload in (
        {"status": "PLACEHOLDER", "echo": FAKE_HARNESS_AUTH},
        {"status": "PLACEHOLDER", "echo": FAKE_HARNESS_BASE_URL},
        {"status": "PLACEHOLDER", "credential": "DEMO_NON_PROD_FAKE_CREDENTIAL"},
    ):
        result = run_local_api_football_http_smoke_harness(
            request_callable=RecordingRequestCallable(payload),
            environ=fake_harness_environ(),
        )

        assert result.executed is False
        assert result.status == LOCAL_HTTP_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS
        assert result.payload_hash is None
        assert_result_has_no_local_http_smoke_leaks(result)


def test_local_http_smoke_harness_output_validator_rejects_constructed_leaks() -> None:
    unsafe_result = LocalApiFootballHttpSmokeHarnessResult(
        status=FAKE_HARNESS_AUTH,
        executed=True,
        payload_hash="placeholder_hash",
    )

    with pytest.raises(ApiFootballSmokeDisabledError, match="non-public provider material"):
        assert_local_api_football_http_smoke_harness_output_safe(
            unsafe_result,
            environ=fake_harness_environ(),
        )


def test_local_http_smoke_harness_main_prints_safe_disabled_result(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    serialized = captured.out.lower()

    assert exit_code == 0
    assert payload["status"] == LOCAL_HTTP_SMOKE_DISABLED_STATUS
    assert payload["executed"] is False
    assert payload["provider"] == LOCAL_HTTP_SMOKE_PROVIDER
    assert payload["mode"] == LOCAL_HTTP_SMOKE_MODE
    assert payload["db_writes"] is False
    assert payload["prediction_created"] is False
    assert payload["betting_created"] is False
    for env_name in API_FOOTBALL_SMOKE_ENV_NAMES:
        assert env_name.lower() not in serialized


def test_local_http_smoke_harness_has_no_concrete_http_client() -> None:
    source = Path("scripts/api_football_local_smoke_harness.py").read_text(encoding="utf-8").lower()

    for forbidden in ("requests", "httpx", "aiohttp", "urllib", "urlopen", "create_connection"):
        assert forbidden not in source


def test_local_http_smoke_harness_is_not_imported_by_fastapi_routes() -> None:
    api_sources = [
        *Path("app/api").rglob("*.py"),
        Path("app/main.py"),
    ]

    for source_path in api_sources:
        assert "api_football_local_smoke_harness" not in source_path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/providers/smoke",
        "/api/v1/providers/smoke/run",
        "/api/v1/providers/manual-smoke",
        "/api/v1/providers/local-smoke",
        "/api/v1/providers/local-http-smoke",
        "/api/v1/providers/harness",
        "/api/v1/providers/runbook",
        "/api/v1/providers/api-football/manual-smoke",
        "/api/v1/providers/api-football/local-http-smoke",
        "/api/v1/providers/api-football/harness",
    ],
)
def test_local_http_smoke_harness_has_no_public_endpoint(path: str) -> None:
    response = client.get(path)

    assert response.status_code == 404


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_provider_readiness_dangerous_methods_stay_absent(method: str) -> None:
    response = client.request(method.upper(), "/api/v1/providers/readiness", json={})

    assert response.status_code == 405
