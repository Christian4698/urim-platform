from pathlib import Path
import socket

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.providers.onboarding_gate import (
    build_provider_onboarding_gate,
    refuse_provider_activation,
)
from app.modules.providers.secret_safety import (
    FUTURE_PROVIDER_SECRET_ENV_NAMES,
    validate_env_example_provider_placeholders,
)
from app.schemas.providers import (
    PROVIDER_ACTIVATION_BLOCKING_REASONS,
    PROVIDER_SECRET_READINESS_CATEGORIES,
    ProviderActivationChecklist,
    ProviderSecretReadiness,
)

client = TestClient(app)
REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_EXAMPLE = REPO_ROOT / ".env.example"


def test_provider_onboarding_gate_blocks_activation_by_default() -> None:
    gate = build_provider_onboarding_gate()

    assert gate.status == "blocked_until_real_provider_audit"
    assert gate.can_activate is False
    assert gate.providers_enabled is False
    assert gate.api_football_connected is False
    assert gate.network_calls_enabled is False
    assert gate.db_ingestion_enabled is False
    assert gate.blocking_reasons == list(PROVIDER_ACTIVATION_BLOCKING_REASONS)
    assert gate.secret_readiness.configured is False
    assert gate.secret_readiness.public_env_var_names_exposed is False


def test_provider_activation_guard_refuses_even_with_constructed_inputs() -> None:
    checklist = ProviderActivationChecklist.model_construct(
        license_validated=True,
        quotas_known=True,
        rate_limits_known=True,
        latency_measured=True,
        pagination_documented=True,
        retries_defined=True,
        circuit_breaker_defined=True,
        redaction_verified=True,
        monitoring_defined=True,
        reconciliation_strategy_defined=True,
        anonymized_real_golden_payloads_available=True,
        security_audit_validated=True,
        secure_env_secret_management_validated=True,
    )
    secret_readiness = ProviderSecretReadiness.model_construct(
        configured=True,
        secret_values_present=True,
        public_env_var_names_exposed=True,
    )

    gate = refuse_provider_activation(checklist=checklist, secret_readiness=secret_readiness)

    assert gate.can_activate is False
    assert gate.providers_enabled is False
    assert "phase_14_keeps_real_provider_activation_blocked" in gate.blocking_reasons
    assert gate.checklist.license_validated is False
    assert gate.checklist.quotas_known is False
    assert gate.checklist.rate_limits_known is False
    assert gate.checklist.secure_env_secret_management_validated is False
    assert gate.secret_readiness.configured is False
    assert gate.secret_readiness.secret_values_present is False
    assert gate.secret_readiness.public_env_var_names_exposed is False


def test_refuse_provider_activation_documents_structural_blocking() -> None:
    doc = refuse_provider_activation.__doc__

    assert doc is not None
    assert "Literal[False]" in doc
    assert "does not contain conditional activation logic" in doc


def test_build_provider_onboarding_gate_resets_bypassed_inputs() -> None:
    checklist = ProviderActivationChecklist.model_construct(
        license_validated=True,
        quotas_known=True,
        rate_limits_known=True,
        latency_measured=True,
        pagination_documented=True,
        retries_defined=True,
        circuit_breaker_defined=True,
        redaction_verified=True,
        monitoring_defined=True,
        reconciliation_strategy_defined=True,
        anonymized_real_golden_payloads_available=True,
        security_audit_validated=True,
        secure_env_secret_management_validated=True,
    )
    secret_readiness = ProviderSecretReadiness.model_construct(
        configured=True,
        secret_values_present=True,
        public_env_var_names_exposed=True,
    )

    gate = build_provider_onboarding_gate(checklist=checklist, secret_readiness=secret_readiness)

    assert gate.checklist.model_dump() == ProviderActivationChecklist().model_dump()
    assert gate.secret_readiness.model_dump() == ProviderSecretReadiness().model_dump()


def test_provider_readiness_exposes_gate_without_secret_env_names() -> None:
    response = client.get("/api/v1/providers/readiness")

    assert response.status_code == 200
    payload = response.json()
    gate = payload["onboarding_gate"]
    body = response.text

    assert gate["status"] == "blocked_until_real_provider_audit"
    assert gate["can_activate"] is False
    assert gate["providers_enabled"] is False
    assert gate["secret_readiness"]["secret_categories"] == list(PROVIDER_SECRET_READINESS_CATEGORIES)
    assert "api_key" not in gate["secret_readiness"]["secret_categories"]
    assert "secret" not in " ".join(gate["secret_readiness"]["secret_categories"])
    assert gate["secret_readiness"]["expected_secret_count"] == len(PROVIDER_SECRET_READINESS_CATEGORIES)
    assert gate["secret_readiness"]["configured"] is False
    assert gate["secret_readiness"]["secret_values_present"] is False
    assert gate["secret_readiness"]["public_env_var_names_exposed"] is False

    for env_name in FUTURE_PROVIDER_SECRET_ENV_NAMES:
        assert env_name not in body


def test_sandbox_status_exposes_blocked_gate_without_secret_env_names() -> None:
    response = client.get("/api/v1/providers/sandbox/status")

    assert response.status_code == 200
    body = response.text
    gate = response.json()["onboarding_gate"]

    assert gate["status"] == "blocked_until_real_provider_audit"
    assert gate["can_activate"] is False
    assert gate["providers_enabled"] is False
    for env_name in FUTURE_PROVIDER_SECRET_ENV_NAMES:
        assert env_name not in body


def test_future_provider_secret_env_names_are_empty_placeholders_only() -> None:
    env_bytes = ENV_EXAMPLE.read_bytes()
    env_lines = env_bytes.decode("utf-8").splitlines()

    assert b"\r\n" not in env_bytes
    validate_env_example_provider_placeholders(env_bytes.decode("utf-8"))

    for env_name in FUTURE_PROVIDER_SECRET_ENV_NAMES:
        assert f"{env_name}=" in env_lines


def test_provider_onboarding_gate_does_not_open_network_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_create_connection(*args: object, **kwargs: object) -> None:
        raise AssertionError("provider onboarding gate must not open network sockets")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    response = client.get("/api/v1/providers/readiness")

    assert response.status_code == 200
    assert response.json()["onboarding_gate"]["network_calls_enabled"] is False
