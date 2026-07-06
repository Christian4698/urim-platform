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
from scripts import api_football_first_real_local_smoke as first_real_smoke
from scripts.api_football_first_real_local_smoke import (
    FIRST_REAL_LOCAL_SMOKE_COMPLETED_STATUS,
    FIRST_REAL_LOCAL_SMOKE_MODE,
    FIRST_REAL_LOCAL_SMOKE_NOT_READY_STATUS,
    FIRST_REAL_LOCAL_SMOKE_PROVIDER,
    FIRST_REAL_LOCAL_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS,
    ApiFootballFirstRealLocalSmokeResult,
    assert_api_football_first_real_local_smoke_output_safe,
    run_api_football_first_real_local_smoke,
)
from scripts.api_football_local_preflight import LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES

client = TestClient(app)

REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "43_API_FOOTBALL_FIRST_REAL_LOCAL_SMOKE_EXECUTION.md"
PHASE_24_PLAN_PATHS = (
    REPO_ROOT / "docs" / "exec-plans" / "active" / "024-phase-24-api-football-first-real-local-smoke-execution.md",
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "024-phase-24-api-football-first-real-local-smoke-execution.md",
)
PUBLIC_PHASE_24_DOCS = (
    DOC_PATH,
    REPO_ROOT / "docs" / "21_API_AND_DATABASE_SPEC.md",
    REPO_ROOT / "docs" / "index.md",
    REPO_ROOT / "apps" / "api" / "README.md",
)
SAFE_REPO_CHECKS = {
    "public_smoke_routes_absent": True,
    "provider_material_absent": True,
    "git_status_clean_recommended": True,
}
FAKE_EXECUTION_AUTH = "DEMO_NON_PROD_FAKE_PHASE24_AUTH_MATERIAL"
FAKE_EXECUTION_REFERENCE = "DEMO_NON_PROD_FAKE_PHASE24_PROVIDER_REFERENCE"


class RecordingRequestCallable:
    def __init__(self, payload: Mapping[str, Any] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.payload = dict(
            payload
            or {
                "marker": "DEMO_NON_PROD",
                "payload_state": "NO_PUBLIC_PROVIDER_DATA",
                "status": "PLACEHOLDER_PHASE24_FIRST_REAL_LOCAL_SMOKE_OK",
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


def phase_24_plan_path() -> Path:
    for plan_path in PHASE_24_PLAN_PATHS:
        if plan_path.exists():
            return plan_path
    candidates = ", ".join(str(plan_path) for plan_path in PHASE_24_PLAN_PATHS)
    raise AssertionError(f"Phase 24 exec plan missing from active/completed: {candidates}")


def fake_execution_environ(**overrides: str | None) -> dict[str, str]:
    environ = {
        API_FOOTBALL_SMOKE_ENV_NAMES[0]: "true",
        API_FOOTBALL_SMOKE_ENV_NAMES[1]: FAKE_EXECUTION_AUTH,
        API_FOOTBALL_SMOKE_ENV_NAMES[2]: FAKE_EXECUTION_REFERENCE,
        API_FOOTBALL_SMOKE_ENV_NAMES[3]: "true",
        API_FOOTBALL_SMOKE_ENV_NAMES[4]: "true",
        LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES[0]: "true",
        LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES[1]: "true",
        LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES[2]: "true",
        "APP_ENV": "development",
    }
    for key, value in overrides.items():
        if value is None:
            environ.pop(key, None)
        else:
            environ[key] = value
    return environ


def assert_summary_has_no_execution_leaks(summary: dict[str, object]) -> None:
    serialized = json.dumps(summary, sort_keys=True).lower()
    forbidden_fragments = (
        FAKE_EXECUTION_AUTH.lower(),
        FAKE_EXECUTION_REFERENCE.lower(),
        "http://",
        "https://",
        "api-football.com",
        "api-sports",
        "rapidapi",
        "x-rapidapi",
        "api_key",
        "authorization",
        "bearer",
        "credential",
        "provider_credentials",
        "password",
        "secret",
        "token",
        "raw_payload",
        "smoke_payload",
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized
    for env_name in (*API_FOOTBALL_SMOKE_ENV_NAMES, *LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES):
        assert env_name.lower() not in serialized


def test_first_real_local_smoke_refuses_by_default_without_calling_callable() -> None:
    request_callable = RecordingRequestCallable()

    result = run_api_football_first_real_local_smoke(
        environ={},
        request_callable=request_callable,
        repo_checks=SAFE_REPO_CHECKS,
    )

    assert result.status == FIRST_REAL_LOCAL_SMOKE_NOT_READY_STATUS
    assert result.executed is False
    assert result.provider == FIRST_REAL_LOCAL_SMOKE_PROVIDER
    assert result.mode == FIRST_REAL_LOCAL_SMOKE_MODE
    assert result.payload_hash is None
    assert result.payload_top_level_keys == ()
    assert result.db_writes is False
    assert result.prediction_created is False
    assert result.betting_created is False
    assert "smoke_mode_not_explicitly_enabled" in result.blocking_reasons
    assert "local_auth_material_missing" in result.blocking_reasons
    assert "local_provider_reference_missing" in result.blocking_reasons
    assert "non_production_confirmation_missing" in result.blocking_reasons
    assert request_callable.calls == []
    assert_summary_has_no_execution_leaks(result.public_safe_summary())


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        ({"APP_ENV": "production"}, "production_environment_refused"),
        ({API_FOOTBALL_SMOKE_ENV_NAMES[0]: "false"}, "smoke_mode_not_explicitly_enabled"),
        ({API_FOOTBALL_SMOKE_ENV_NAMES[1]: None}, "local_auth_material_missing"),
        ({API_FOOTBALL_SMOKE_ENV_NAMES[2]: None}, "local_provider_reference_missing"),
        ({API_FOOTBALL_SMOKE_ENV_NAMES[3]: "false"}, "read_only_confirmation_missing"),
        ({API_FOOTBALL_SMOKE_ENV_NAMES[4]: "false"}, "non_production_confirmation_missing"),
        ({LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES[0]: "false"}, "no_db_write_confirmation_missing"),
        ({LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES[1]: "false"}, "no_prediction_confirmation_missing"),
        ({LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES[2]: "false"}, "no_betting_confirmation_missing"),
    ],
)
def test_first_real_local_smoke_refuses_missing_execution_gates(
    overrides: dict[str, str | None],
    expected_reason: str,
) -> None:
    request_callable = RecordingRequestCallable()

    result = run_api_football_first_real_local_smoke(
        environ=fake_execution_environ(**overrides),
        request_callable=request_callable,
        repo_checks=SAFE_REPO_CHECKS,
    )

    assert result.status == FIRST_REAL_LOCAL_SMOKE_NOT_READY_STATUS
    assert result.executed is False
    assert expected_reason in result.blocking_reasons
    assert request_callable.calls == []
    assert_summary_has_no_execution_leaks(result.public_safe_summary())


@pytest.mark.parametrize(
    ("repo_checks", "expected_reason"),
    [
        ({"git_status_clean_recommended": False}, "git_status_not_clean"),
        ({"public_smoke_routes_absent": False}, "public_smoke_route_present"),
        ({"provider_material_absent": False}, "provider_material_present_in_repo"),
    ],
)
def test_first_real_local_smoke_refuses_unsafe_repo_checks(
    repo_checks: dict[str, bool],
    expected_reason: str,
) -> None:
    request_callable = RecordingRequestCallable()

    result = run_api_football_first_real_local_smoke(
        environ=fake_execution_environ(),
        request_callable=request_callable,
        repo_checks={**SAFE_REPO_CHECKS, **repo_checks},
    )

    assert result.status == FIRST_REAL_LOCAL_SMOKE_NOT_READY_STATUS
    assert result.executed is False
    assert expected_reason in result.blocking_reasons
    assert request_callable.calls == []
    assert_summary_has_no_execution_leaks(result.public_safe_summary())


def test_first_real_local_smoke_refuses_when_provider_gate_is_not_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    request_callable = RecordingRequestCallable()
    monkeypatch.setattr(first_real_smoke, "_provider_gate_blocked", lambda: False)

    result = run_api_football_first_real_local_smoke(
        environ=fake_execution_environ(),
        request_callable=request_callable,
        repo_checks=SAFE_REPO_CHECKS,
    )

    assert result.status == FIRST_REAL_LOCAL_SMOKE_NOT_READY_STATUS
    assert result.executed is False
    assert "provider_activation_gate_not_blocked" in result.blocking_reasons
    assert request_callable.calls == []
    assert_summary_has_no_execution_leaks(result.public_safe_summary())


def test_first_real_local_smoke_success_uses_fake_callable_only() -> None:
    payload = {
        "marker": "DEMO_NON_PROD",
        "payload_state": "NO_PUBLIC_PROVIDER_DATA",
        "status": "PLACEHOLDER_PHASE24_FIRST_REAL_LOCAL_SMOKE_OK",
    }
    request_callable = RecordingRequestCallable(payload)

    result = run_api_football_first_real_local_smoke(
        environ=fake_execution_environ(),
        request_callable=request_callable,
        repo_checks=SAFE_REPO_CHECKS,
        query={"scope": "phase24_first_real_local_smoke_execution"},
    )

    assert request_callable.calls == [
        {
            "base_url": FAKE_EXECUTION_REFERENCE,
            "auth_material": FAKE_EXECUTION_AUTH,
            "query": {"scope": "phase24_first_real_local_smoke_execution"},
        }
    ]
    assert result.status == FIRST_REAL_LOCAL_SMOKE_COMPLETED_STATUS
    assert result.executed is True
    assert result.payload_hash == stable_raw_hash({"smoke_payload": payload})
    assert result.payload_top_level_keys == ("marker", "payload_state", "status")
    assert result.db_writes is False
    assert result.prediction_created is False
    assert result.betting_created is False
    assert result.blocking_reasons == ()
    assert_summary_has_no_execution_leaks(result.public_safe_summary())


def test_first_real_local_smoke_refuses_unsafe_fake_payload_without_leaking() -> None:
    result = run_api_football_first_real_local_smoke(
        environ=fake_execution_environ(),
        request_callable=RecordingRequestCallable({"status": "PLACEHOLDER", "echo": FAKE_EXECUTION_AUTH}),
        repo_checks=SAFE_REPO_CHECKS,
    )

    assert result.status == FIRST_REAL_LOCAL_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS
    assert result.executed is False
    assert result.payload_hash is None
    assert result.payload_top_level_keys == ()
    assert result.blocking_reasons == ("unsafe_harness_output_refused",)
    assert_summary_has_no_execution_leaks(result.public_safe_summary())


def test_first_real_local_smoke_output_validator_rejects_constructed_leaks() -> None:
    unsafe_result = ApiFootballFirstRealLocalSmokeResult(
        status=FAKE_EXECUTION_AUTH,
        executed=True,
        payload_hash="placeholder_hash",
    )

    with pytest.raises(ApiFootballSmokeDisabledError, match="non-public provider material"):
        assert_api_football_first_real_local_smoke_output_safe(
            unsafe_result,
            environ=fake_execution_environ(),
        )


def test_first_real_local_smoke_refusal_paths_do_not_open_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_create_connection(*args: object, **kwargs: object) -> None:
        raise AssertionError("Phase 24 refusal paths must not open sockets")

    def fail_urlopen(*args: object, **kwargs: object) -> None:
        raise AssertionError("Phase 24 refusal paths must not open provider URLs")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)
    monkeypatch.setattr(first_real_smoke, "urlopen", fail_urlopen)

    result = run_api_football_first_real_local_smoke(environ={}, repo_checks=SAFE_REPO_CHECKS)

    assert result.executed is False
    assert result.status == FIRST_REAL_LOCAL_SMOKE_NOT_READY_STATUS


def test_first_real_local_smoke_injected_callable_path_does_not_use_urlopen(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_urlopen(*args: object, **kwargs: object) -> None:
        raise AssertionError("injected fake callable path must not use the standard-library opener")

    monkeypatch.setattr(first_real_smoke, "urlopen", fail_urlopen)

    result = run_api_football_first_real_local_smoke(
        environ=fake_execution_environ(),
        request_callable=RecordingRequestCallable(),
        repo_checks=SAFE_REPO_CHECKS,
    )

    assert result.status == FIRST_REAL_LOCAL_SMOKE_COMPLETED_STATUS
    assert result.executed is True


def test_first_real_local_smoke_source_has_no_third_party_http_client_dependency() -> None:
    source = Path("scripts/api_football_first_real_local_smoke.py").read_text(encoding="utf-8").lower()

    for forbidden in ("requests", "httpx", "aiohttp"):
        assert forbidden not in source


def test_first_real_local_smoke_is_not_imported_by_fastapi() -> None:
    fastapi_sources = [
        *Path("app/api").rglob("*.py"),
        Path("app/main.py"),
    ]

    for source_path in fastapi_sources:
        assert "api_football_first_real_local_smoke" not in source_path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/providers/smoke-execution",
        "/api/v1/providers/first-real-smoke",
        "/api/v1/providers/first-real-local-smoke",
        "/api/v1/providers/first-real-local-smoke-execution",
        "/api/v1/providers/api-football/first-real-smoke",
        "/api/v1/providers/api-football/first-real-local-smoke",
        "/api/v1/providers/api-football/first-real-local-smoke-execution",
        "/api/v1/providers/api-football/smoke-execution",
    ],
)
def test_first_real_local_smoke_execution_adds_no_public_endpoint(path: str) -> None:
    response = client.get(path)

    assert response.status_code == 404


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_first_real_local_smoke_dangerous_methods_stay_absent(method: str) -> None:
    response = client.request(method.upper(), "/api/v1/providers", json={})

    assert response.status_code == 405


def test_first_real_local_smoke_provider_list_mentions_script_only_safeguard() -> None:
    response = client.get("/api/v1/providers")

    assert response.status_code == 200
    safeguards = "\n".join(response.json()["safeguards"]).lower()
    assert "first real local smoke execution is script-only" in safeguards
    assert "not exposed through fastapi" in safeguards


def test_first_real_local_smoke_docs_are_public_safe() -> None:
    public_docs = "\n".join(
        path.read_text(encoding="utf-8") for path in (*PUBLIC_PHASE_24_DOCS, phase_24_plan_path())
    ).lower()

    assert "phase 24" in public_docs
    assert "43_api_football_first_real_local_smoke_execution.md" in public_docs
    assert "phase-24-api-football-first-real-local-smoke-execution" in public_docs
    assert "first_real_local_smoke_only" in public_docs

    forbidden_fragments = (
        "http://",
        "https://",
        "api-football.com",
        "api-sports",
        "rapidapi",
        "x-rapidapi",
        "api_key=",
        "apikey",
        "smoke_payload",
        FAKE_EXECUTION_AUTH.lower(),
        FAKE_EXECUTION_REFERENCE.lower(),
    )
    for fragment in forbidden_fragments:
        assert fragment not in public_docs

    for env_name in (*API_FOOTBALL_SMOKE_ENV_NAMES, *LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES):
        assert env_name.lower() not in public_docs


def test_first_real_local_smoke_does_not_touch_db_migrations_frontend_or_env_example() -> None:
    guarded_paths = [
        REPO_ROOT / "apps" / "api" / "alembic",
        REPO_ROOT / "apps" / "api" / "app" / "db",
        REPO_ROOT / "apps" / "web",
        REPO_ROOT / ".env.example",
    ]

    for guarded_path in guarded_paths:
        if not guarded_path.exists():
            continue
        paths = [guarded_path] if guarded_path.is_file() else list(guarded_path.rglob("*"))
        for source_path in paths:
            if source_path.is_file():
                source = source_path.read_text(encoding="utf-8", errors="ignore").lower()
                assert "phase-24-api-football-first-real-local-smoke-execution" not in source
                assert "first_real_local_smoke_only" not in source
                assert "api_football_first_real_local_smoke" not in source
