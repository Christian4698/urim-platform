import json
import socket
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.providers.api_football_smoke_client import (
    API_FOOTBALL_SMOKE_ENV_NAMES,
    ApiFootballSmokeDisabledError,
)
from scripts.api_football_local_preflight import (
    LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES,
    LOCAL_SECRET_ENV_PREFLIGHT_MODE,
    LOCAL_SECRET_ENV_PREFLIGHT_NOT_READY_STATUS,
    LOCAL_SECRET_ENV_PREFLIGHT_PROVIDER,
    LOCAL_SECRET_ENV_PREFLIGHT_READY_STATUS,
    LocalApiFootballSecretEnvPreflightResult,
    assert_local_secret_env_preflight_output_safe,
    main,
    run_local_api_football_secret_env_preflight,
)

client = TestClient(app)

REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "42_API_FOOTBALL_LOCAL_SECRET_ENV_PREFLIGHT.md"
PHASE_23_PLAN_PATHS = (
    REPO_ROOT / "docs" / "exec-plans" / "completed" / "023-phase-23-api-football-local-secret-env-preflight.md",
    REPO_ROOT / "docs" / "exec-plans" / "active" / "023-phase-23-api-football-local-secret-env-preflight.md",
)


def phase_23_plan_path() -> Path:
    for plan_path in PHASE_23_PLAN_PATHS:
        if plan_path.exists():
            return plan_path
    candidates = ", ".join(str(plan_path) for plan_path in PHASE_23_PLAN_PATHS)
    raise AssertionError(f"Phase 23 exec plan missing from completed/active: {candidates}")


PUBLIC_PHASE_23_DOCS = (
    DOC_PATH,
    phase_23_plan_path(),
    REPO_ROOT / "docs" / "21_API_AND_DATABASE_SPEC.md",
    REPO_ROOT / "docs" / "index.md",
    REPO_ROOT / "apps" / "api" / "README.md",
)
SAFE_REPO_CHECKS = {
    "public_smoke_routes_absent": True,
    "provider_material_absent": True,
    "git_status_clean_recommended": True,
}
FAKE_PREFLIGHT_AUTH = "DEMO_NON_PROD_FAKE_PHASE23_AUTH_MATERIAL"
FAKE_PREFLIGHT_REFERENCE = "DEMO_NON_PROD_FAKE_PHASE23_PROVIDER_REFERENCE"


def fake_preflight_environ(**overrides: str | None) -> dict[str, str]:
    environ = {
        API_FOOTBALL_SMOKE_ENV_NAMES[0]: "true",
        API_FOOTBALL_SMOKE_ENV_NAMES[1]: FAKE_PREFLIGHT_AUTH,
        API_FOOTBALL_SMOKE_ENV_NAMES[2]: FAKE_PREFLIGHT_REFERENCE,
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


def assert_summary_has_no_preflight_leaks(summary: dict[str, object]) -> None:
    serialized = json.dumps(summary, sort_keys=True).lower()
    forbidden_fragments = (
        FAKE_PREFLIGHT_AUTH.lower(),
        FAKE_PREFLIGHT_REFERENCE.lower(),
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
        "token",
        "raw_payload",
        "smoke_payload",
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized
    for env_name in (*API_FOOTBALL_SMOKE_ENV_NAMES, *LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES):
        assert env_name.lower() not in serialized


def test_local_secret_env_preflight_not_ready_by_default() -> None:
    result = run_local_api_football_secret_env_preflight(environ={}, repo_checks=SAFE_REPO_CHECKS)

    assert result.status == LOCAL_SECRET_ENV_PREFLIGHT_NOT_READY_STATUS
    assert result.ready_for_manual_smoke_attempt is False
    assert result.provider == LOCAL_SECRET_ENV_PREFLIGHT_PROVIDER
    assert result.mode == LOCAL_SECRET_ENV_PREFLIGHT_MODE
    assert result.secrets_detected_as_present is False
    assert result.provider_reference_present is False
    assert result.db_writes is False
    assert result.prediction_created is False
    assert result.betting_created is False
    assert "smoke_mode_not_explicitly_enabled" in result.blocking_reasons
    assert "local_auth_material_missing" in result.blocking_reasons
    assert "local_provider_reference_missing" in result.blocking_reasons
    assert_summary_has_no_preflight_leaks(result.public_safe_summary())


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        ({"APP_ENV": "production"}, "production_environment_refused"),
        ({API_FOOTBALL_SMOKE_ENV_NAMES[0]: "false"}, "smoke_mode_not_explicitly_enabled"),
        ({API_FOOTBALL_SMOKE_ENV_NAMES[3]: "false"}, "read_only_confirmation_missing"),
        ({LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES[0]: "false"}, "no_db_write_confirmation_missing"),
        ({LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES[1]: "false"}, "no_prediction_confirmation_missing"),
        ({LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES[2]: "false"}, "no_betting_confirmation_missing"),
        ({API_FOOTBALL_SMOKE_ENV_NAMES[1]: None}, "local_auth_material_missing"),
        ({API_FOOTBALL_SMOKE_ENV_NAMES[2]: None}, "local_provider_reference_missing"),
    ],
)
def test_local_secret_env_preflight_refuses_missing_local_conditions(
    overrides: dict[str, str | None],
    expected_reason: str,
) -> None:
    result = run_local_api_football_secret_env_preflight(
        environ=fake_preflight_environ(**overrides),
        repo_checks=SAFE_REPO_CHECKS,
    )

    assert result.status == LOCAL_SECRET_ENV_PREFLIGHT_NOT_READY_STATUS
    assert result.ready_for_manual_smoke_attempt is False
    assert expected_reason in result.blocking_reasons
    assert_summary_has_no_preflight_leaks(result.public_safe_summary())


@pytest.mark.parametrize(
    ("repo_checks", "expected_reason"),
    [
        ({"public_smoke_routes_absent": False, "provider_material_absent": True}, "public_smoke_route_present"),
        ({"public_smoke_routes_absent": True, "provider_material_absent": False}, "provider_material_present_in_repo"),
    ],
)
def test_local_secret_env_preflight_refuses_unsafe_repo_checks(
    repo_checks: dict[str, bool],
    expected_reason: str,
) -> None:
    result = run_local_api_football_secret_env_preflight(
        environ=fake_preflight_environ(),
        repo_checks={**SAFE_REPO_CHECKS, **repo_checks},
    )

    assert result.status == LOCAL_SECRET_ENV_PREFLIGHT_NOT_READY_STATUS
    assert result.ready_for_manual_smoke_attempt is False
    assert expected_reason in result.blocking_reasons
    assert_summary_has_no_preflight_leaks(result.public_safe_summary())


def test_local_secret_env_preflight_ready_with_safe_local_conditions() -> None:
    result = run_local_api_football_secret_env_preflight(
        environ=fake_preflight_environ(),
        repo_checks={**SAFE_REPO_CHECKS, "git_status_clean_recommended": False},
    )

    assert result.status == LOCAL_SECRET_ENV_PREFLIGHT_READY_STATUS
    assert result.ready_for_manual_smoke_attempt is True
    assert result.secrets_detected_as_present is True
    assert result.provider_reference_present is True
    assert result.git_status_clean_recommended is False
    assert result.blocking_reasons == ()
    assert result.db_writes is False
    assert result.prediction_created is False
    assert result.betting_created is False
    assert_summary_has_no_preflight_leaks(result.public_safe_summary())


def test_local_secret_env_preflight_does_not_open_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_create_connection(*args: object, **kwargs: object) -> None:
        raise AssertionError("local secret env preflight must not open sockets")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    result = run_local_api_football_secret_env_preflight(
        environ=fake_preflight_environ(),
        repo_checks=SAFE_REPO_CHECKS,
    )

    assert result.ready_for_manual_smoke_attempt is True


def test_local_secret_env_preflight_output_validator_rejects_constructed_leaks() -> None:
    unsafe_result = LocalApiFootballSecretEnvPreflightResult(status=FAKE_PREFLIGHT_AUTH)

    with pytest.raises(ApiFootballSmokeDisabledError, match="non-public material"):
        assert_local_secret_env_preflight_output_safe(
            unsafe_result,
            environ=fake_preflight_environ(),
        )


def test_local_secret_env_preflight_main_prints_safe_result(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    for env_name in (*API_FOOTBALL_SMOKE_ENV_NAMES, *LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES):
        monkeypatch.delenv(env_name, raising=False)
    monkeypatch.setenv("APP_ENV", "development")

    exit_code = main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["status"] == LOCAL_SECRET_ENV_PREFLIGHT_NOT_READY_STATUS
    assert payload["ready_for_manual_smoke_attempt"] is False
    assert payload["db_writes"] is False
    assert payload["prediction_created"] is False
    assert payload["betting_created"] is False
    assert_summary_has_no_preflight_leaks(payload)


def test_local_secret_env_preflight_source_has_no_provider_client_or_network_openers() -> None:
    source = Path("scripts/api_football_local_preflight.py").read_text(encoding="utf-8").lower()

    for forbidden in ("requests", "httpx", "aiohttp", "urllib", "urlopen", "create_connection"):
        assert forbidden not in source


def test_local_secret_env_preflight_is_not_imported_by_fastapi() -> None:
    fastapi_sources = [
        *Path("app/api").rglob("*.py"),
        Path("app/main.py"),
    ]

    for source_path in fastapi_sources:
        assert "api_football_local_preflight" not in source_path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/providers/smoke",
        "/api/v1/providers/local-smoke",
        "/api/v1/providers/preflight",
        "/api/v1/providers/local-preflight",
        "/api/v1/providers/secret-env-preflight",
        "/api/v1/providers/api-football/preflight",
        "/api/v1/providers/api-football/local-preflight",
        "/api/v1/providers/api-football/secret-env-preflight",
    ],
)
def test_local_secret_env_preflight_adds_no_public_endpoint(path: str) -> None:
    response = client.get(path)

    assert response.status_code == 404


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_local_secret_env_preflight_dangerous_methods_stay_absent(method: str) -> None:
    response = client.request(method.upper(), "/api/v1/providers/readiness", json={})

    assert response.status_code == 405


def test_local_secret_env_preflight_docs_are_public_safe() -> None:
    public_docs = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_PHASE_23_DOCS).lower()

    assert "phase 23" in public_docs
    assert "42_api_football_local_secret_env_preflight.md" in public_docs
    assert "local_secret_env_preflight_only" in public_docs

    forbidden_fragments = (
        "http://",
        "https://",
        "api-football.com",
        "api-sports",
        "rapidapi",
        "x-rapidapi",
        "api_key=",
        "apikey",
        FAKE_PREFLIGHT_AUTH.lower(),
        FAKE_PREFLIGHT_REFERENCE.lower(),
    )
    for fragment in forbidden_fragments:
        assert fragment not in public_docs

    for env_name in (*API_FOOTBALL_SMOKE_ENV_NAMES, *LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES):
        assert env_name.lower() not in public_docs


def test_local_secret_env_preflight_does_not_touch_db_migrations_or_frontend() -> None:
    guarded_paths = [
        REPO_ROOT / "apps" / "api" / "alembic",
        REPO_ROOT / "apps" / "api" / "app" / "db",
        REPO_ROOT / "apps" / "web",
        REPO_ROOT / ".env.example",
    ]

    for guarded_path in guarded_paths:
        paths = [guarded_path] if guarded_path.is_file() else list(guarded_path.rglob("*"))
        for source_path in paths:
            if source_path.is_file():
                source = source_path.read_text(encoding="utf-8", errors="ignore").lower()
                assert "phase-23-api-football-local-secret-env-preflight" not in source
                assert "local_secret_env_preflight_only" not in source
                assert "api_football_local_preflight" not in source
