import json
import socket

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.providers.activation_readiness_final_gate import (
    build_provider_activation_readiness_final_gate,
    refuse_provider_final_activation,
)
from app.modules.providers.secret_safety import (
    FUTURE_PROVIDER_SECRET_ENV_NAMES,
    assert_public_payload_has_no_provider_secret_material,
)
from app.schemas.providers import (
    PROVIDER_FINAL_ACTIVATION_BLOCKING_REASONS,
    PROVIDER_FINAL_ACTIVATION_PREREQUISITES,
    ProviderActivationReadinessFinalGate,
    ProviderFinalActivationPrerequisites,
)

client = TestClient(app)


def test_provider_activation_readiness_final_gate_blocks_by_default() -> None:
    gate = build_provider_activation_readiness_final_gate()

    assert gate.status == "blocked_until_provider_activation_final_gate_approved"
    assert gate.can_activate_provider is False
    assert gate.providers_enabled is False
    assert gate.api_football_connected is False
    assert gate.network_calls_enabled is False
    assert gate.db_ingestion_enabled is False
    assert gate.credentials_accepted is False
    assert gate.production_provider_allowed is False
    assert gate.decision == "blocked"
    assert gate.required_prerequisites == list(PROVIDER_FINAL_ACTIVATION_PREREQUISITES)
    assert gate.blocking_reasons == list(PROVIDER_FINAL_ACTIVATION_BLOCKING_REASONS)
    assert all(value is False for value in gate.prerequisites.model_dump().values())


def test_provider_final_activation_refuses_constructed_dangerous_inputs() -> None:
    prerequisites = ProviderFinalActivationPrerequisites.model_construct(
        license_review_completed=True,
        provider_terms_accepted=True,
        quota_limits_documented=True,
        rate_limits_documented=True,
        latency_budget_defined=True,
        egress_policy_defined=True,
        secret_manager_validated=True,
        log_redaction_validated=True,
        monitoring_defined=True,
        alerting_defined=True,
        reconciliation_plan_defined=True,
        rollback_plan_defined=True,
        anonymized_real_golden_payloads_approved=True,
        security_audit_completed=True,
    )
    final_gate = ProviderActivationReadinessFinalGate.model_construct(
        can_activate_provider=True,
        providers_enabled=True,
        api_football_connected=True,
        network_calls_enabled=True,
        db_ingestion_enabled=True,
        credentials_accepted=True,
        production_provider_allowed=True,
        prerequisites=prerequisites,
        decision="approved",
    )

    gate = refuse_provider_final_activation(prerequisites=prerequisites, final_gate=final_gate)

    assert gate.can_activate_provider is False
    assert gate.providers_enabled is False
    assert gate.api_football_connected is False
    assert gate.network_calls_enabled is False
    assert gate.db_ingestion_enabled is False
    assert gate.credentials_accepted is False
    assert gate.production_provider_allowed is False
    assert gate.decision == "blocked"
    assert gate.prerequisites.model_dump() == ProviderFinalActivationPrerequisites().model_dump()


def test_provider_readiness_exposes_final_gate_without_provider_secrets_or_urls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROVIDER_API_KEY", "DEMO_NON_PROD_FAKE_PHASE15_API_KEY")

    response = client.get("/api/v1/providers/readiness")

    assert response.status_code == 200
    payload = response.json()
    body = response.text.lower()
    gate = payload["activation_readiness_final_gate"]

    assert payload["metadata"]["phase"] == "phase-17-api-football-test-transport-contracts"
    assert gate["can_activate_provider"] is False
    assert gate["providers_enabled"] is False
    assert gate["api_football_connected"] is False
    assert gate["network_calls_enabled"] is False
    assert gate["db_ingestion_enabled"] is False
    assert gate["credentials_accepted"] is False
    assert gate["production_provider_allowed"] is False
    assert gate["decision"] == "blocked"
    assert gate["required_prerequisites"] == list(PROVIDER_FINAL_ACTIVATION_PREREQUISITES)
    assert all(value is False for value in gate["prerequisites"].values())

    assert_public_payload_has_no_provider_secret_material(payload)
    forbidden_fragments = (
        "https://",
        "http://",
        "api-football.com",
        "api-sports",
        "rapidapi",
        "x-rapidapi",
        "demo_non_prod_fake_phase15_api_key",
    )
    for fragment in forbidden_fragments:
        assert fragment not in body
    for env_name in FUTURE_PROVIDER_SECRET_ENV_NAMES:
        assert env_name.lower() not in body


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_provider_readiness_dangerous_methods_remain_absent(method: str) -> None:
    response = client.request(method.upper(), "/api/v1/providers/readiness", json={})

    assert response.status_code == 405


def test_provider_readiness_final_gate_does_not_open_network_socket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*args: object, **kwargs: object) -> None:
        raise AssertionError("provider activation final gate must not open network sockets")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    response = client.get("/api/v1/providers/readiness")

    assert response.status_code == 200
    assert response.json()["activation_readiness_final_gate"]["network_calls_enabled"] is False


def test_provider_activation_readiness_final_gate_serialization_is_public_safe() -> None:
    serialized = json.dumps(build_provider_activation_readiness_final_gate().model_dump(), sort_keys=True)

    forbidden_fragments = (
        "api_key",
        "token",
        "password",
        "provider_credentials",
        "bookmaker",
        "winner",
        "home_score",
        "away_score",
        "https://",
        "http://",
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized.lower()
