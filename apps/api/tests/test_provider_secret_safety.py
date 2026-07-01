from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.providers.secret_safety import (
    FUTURE_PROVIDER_SECRET_ENV_NAMES,
    assert_public_payload_has_no_provider_secret_material,
    build_provider_secret_safety_summary,
    validate_env_example_provider_placeholders,
)

client = TestClient(app)
REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_EXAMPLE = REPO_ROOT / ".env.example"
GITIGNORE = REPO_ROOT / ".gitignore"
FAKE_LOCAL_SECRET_VALUES = {
    "PROVIDER_API_KEY": "DEMO_NON_PROD_FAKE_PHASE12_API_KEY",
    "PROVIDER_API_SECRET": "DEMO_NON_PROD_FAKE_PHASE12_API_SECRET",
    "PROVIDER_WEBHOOK_SECRET": "DEMO_NON_PROD_FAKE_PHASE12_WEBHOOK_SECRET",
    "PROVIDER_CLIENT_ID": "DEMO_NON_PROD_FAKE_PHASE12_CLIENT_ID",
    "PROVIDER_CLIENT_SECRET": "DEMO_NON_PROD_FAKE_PHASE12_CLIENT_SECRET",
}


def test_env_example_provider_secret_placeholders_are_empty_and_lf() -> None:
    env_bytes = ENV_EXAMPLE.read_bytes()
    env_text = env_bytes.decode("utf-8")

    assert b"\r\n" not in env_bytes
    validate_env_example_provider_placeholders(env_text)
    for env_name in FUTURE_PROVIDER_SECRET_ENV_NAMES:
        assert f"{env_name}=" in env_text.splitlines()


def test_gitignore_protects_local_env_files() -> None:
    gitignore_lines = set(GITIGNORE.read_text(encoding="utf-8").splitlines())

    assert ".env" in gitignore_lines
    assert ".env.*" in gitignore_lines
    assert "!.env.example" in gitignore_lines


def test_secret_safety_loader_never_serializes_names_or_values(monkeypatch: pytest.MonkeyPatch) -> None:
    for env_name, secret_value in FAKE_LOCAL_SECRET_VALUES.items():
        monkeypatch.setenv(env_name, secret_value)

    summary = build_provider_secret_safety_summary()
    serialized_summary = summary.model_dump_json()

    assert summary.configured is False
    assert summary.missing is True
    assert summary.providers_enabled is False
    assert summary.activation_allowed is False
    assert summary.raw_values_exposed is False
    assert summary.public_env_var_names_exposed is False
    assert summary.category_count == len(summary.secret_categories)
    assert summary.expected_secret_count == len(FUTURE_PROVIDER_SECRET_ENV_NAMES)

    for env_name, secret_value in FAKE_LOCAL_SECRET_VALUES.items():
        assert env_name not in serialized_summary
        assert secret_value not in serialized_summary


def test_secret_exposure_guard_rejects_public_payload_names_and_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROVIDER_API_KEY", "DEMO_NON_PROD_FAKE_PHASE12_API_KEY")

    with pytest.raises(ValueError, match="public payload exposes provider secret metadata"):
        assert_public_payload_has_no_provider_secret_material({"leak": "PROVIDER_API_KEY"})

    with pytest.raises(ValueError, match="public payload exposes provider secret material"):
        assert_public_payload_has_no_provider_secret_material(
            {"leak": "DEMO_NON_PROD_FAKE_PHASE12_API_KEY"}
        )


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/providers/readiness",
        "/api/v1/providers/sandbox/status",
    ],
)
def test_public_provider_responses_hide_local_secret_names_and_values(
    path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for env_name, secret_value in FAKE_LOCAL_SECRET_VALUES.items():
        monkeypatch.setenv(env_name, secret_value)

    response = client.get(path)
    body = response.text

    assert response.status_code == 200
    assert_public_payload_has_no_provider_secret_material(response.json())
    for env_name, secret_value in FAKE_LOCAL_SECRET_VALUES.items():
        assert env_name not in body
        assert secret_value not in body

    payload = response.json()
    secret_safety = payload["secret_safety"]
    assert secret_safety["configured"] is False
    assert secret_safety["missing"] is True
    assert secret_safety["providers_enabled"] is False
    assert secret_safety["activation_allowed"] is False
    assert secret_safety["raw_values_exposed"] is False
    assert secret_safety["public_env_var_names_exposed"] is False
