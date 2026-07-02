from datetime import UTC, datetime
import json
import socket

from fastapi.testclient import TestClient

from app.core.security import SECURITY_HEADERS
from app.main import app
from app.modules.providers.contracts import SportsDataProviderProtocol
from app.modules.providers.quality import build_quality_report
from app.modules.providers.sandbox import (
    SANDBOX_GOLDEN_PAYLOADS,
    SANDBOX_MODE,
    SANDBOX_PROVIDER_ID,
    SandboxProviderAdapter,
    stable_raw_hash,
)
from app.schemas.providers import (
    PROVIDER_ONBOARDING_REQUIREMENTS,
    PROVIDER_PREFLIGHT_BLOCKING_REASONS,
    PROVIDER_PREFLIGHT_FUTURE_CHECKLIST,
    RATE_LIMIT_QUOTA_CONTRACTS,
    RECONCILIATION_READINESS_REQUIREMENTS,
    SANDBOX_INTEGRATION_FLOW,
)
from tests.helpers.payload_helpers import walk_keys, walk_values

client = TestClient(app)


def test_sandbox_adapter_satisfies_provider_protocol() -> None:
    assert isinstance(SandboxProviderAdapter(), SportsDataProviderProtocol)


def test_official_result_envelope_remains_sandbox_only_extension() -> None:
    adapter = SandboxProviderAdapter()

    assert "official_result_envelope" not in SportsDataProviderProtocol.__dict__
    assert hasattr(adapter, "official_result_envelope")


def test_sandbox_identity_and_capabilities_remain_disabled() -> None:
    adapter = SandboxProviderAdapter()
    identity = adapter.identity()

    assert identity.provider == SANDBOX_PROVIDER_ID
    assert identity.enabled is False
    assert identity.api_football_connected is False
    assert identity.network_calls_enabled is False
    assert identity.credentials_configured is False
    assert identity.production_mock_fallback_allowed is False
    assert adapter.health()["db_ingestion_enabled"] is False
    assert adapter.health()["prediction_creation_enabled"] is False

    for capability in adapter.capabilities():
        assert capability.enabled is False
        assert capability.status == "disabled"


def test_sandbox_golden_payloads_are_non_prod_only() -> None:
    forbidden_keys = {
        "score",
        "scores",
        "result",
        "results",
        "winner",
        "bookmaker",
        "odds",
        "api_key",
        "token",
        "authorization",
        "secret",
        "password",
        "bearer",
        "credential",
        "provider_credentials",
    }
    forbidden_values = {
        "api-football",
        "Manchester",
        "Real Madrid",
        "Barcelona",
        "PSG",
        "Liverpool",
        "Chelsea",
        "Bayern",
        "Juventus",
    }

    assert SANDBOX_GOLDEN_PAYLOADS
    for golden_payload in SANDBOX_GOLDEN_PAYLOADS:
        assert golden_payload["fixture_marker"] == SANDBOX_MODE
        assert golden_payload["provider"] == SANDBOX_PROVIDER_ID
        assert str(golden_payload["provider_event_id"]).startswith("PLACEHOLDER_SANDBOX_EVENT_")
        assert "PLACEHOLDER" in json.dumps(golden_payload)
        assert forbidden_keys.isdisjoint(set(walk_keys(golden_payload)))

        for value in walk_values(golden_payload):
            if isinstance(value, str):
                assert not any(forbidden_value in value for forbidden_value in forbidden_values)


def test_sandbox_mapping_preserves_provenance_and_temporal_order() -> None:
    adapter = SandboxProviderAdapter()
    observations = adapter.fetch_fixtures({"from": datetime(2026, 1, 1, tzinfo=UTC)})

    assert len(observations) == len(SANDBOX_GOLDEN_PAYLOADS)
    for observation, payload in zip(observations, SANDBOX_GOLDEN_PAYLOADS, strict=True):
        assert observation.provider == SANDBOX_PROVIDER_ID
        assert observation.provider_event_id == payload["provider_event_id"]
        assert observation.observed_at.tzinfo is not None
        assert observation.available_at.tzinfo is not None
        assert observation.fetched_at.tzinfo is not None
        assert observation.observed_at <= observation.available_at <= observation.fetched_at
        assert observation.raw_hash == stable_raw_hash(payload)
        assert observation.raw_payload_ref is not None
        assert observation.raw_payload_ref.raw_hash == observation.raw_hash
        assert observation.raw_payload_ref.endpoint == "sandbox://in-memory"
        assert "DEMO_NON_PROD" in observation.quality_flags
        assert "PLACEHOLDER" in json.dumps(observation.data)
        assert build_quality_report(observation).temporal_order_valid is True


def test_sandbox_full_integration_flow_is_contract_only() -> None:
    adapter = SandboxProviderAdapter()
    observation = adapter.fetch_fixture("PLACEHOLDER_SANDBOX_EVENT_001")
    assert observation.raw_payload_ref is not None

    normalized = adapter.normalize(observation.raw_payload_ref)
    mapping = adapter.map_entity(observation)
    temporal_metadata = adapter.temporal_metadata(observation)
    quality_report = adapter.quality_report(observation)
    official_placeholder = adapter.official_result_envelope(observation)

    assert normalized.raw_hash == observation.raw_hash
    assert mapping.provider_entity_type == "sandbox_fixture"
    assert mapping.canonical_entity_id is None
    assert temporal_metadata.available_at == observation.available_at
    assert quality_report.complete_provenance is True
    assert quality_report.temporal_order_valid is True
    assert official_placeholder.learning_source == "post_match_outcomes_only"
    assert "NO_OFFICIAL_DATA" in official_placeholder.quality_flags
    assert official_placeholder.result_payload["data_state"] == "PLACEHOLDER_NO_OFFICIAL_DATA"
    assert "score" not in json.dumps(official_placeholder.result_payload).lower()
    assert "winner" not in json.dumps(official_placeholder.result_payload).lower()


def test_sandbox_payload_summaries_redact_test_only_sensitive_placeholder_values() -> None:
    sensitive_placeholder_payload = {
        "fixture_marker": "DEMO_NON_PROD",
        "provider": SANDBOX_PROVIDER_ID,
        "provider_event_id": "PLACEHOLDER_SANDBOX_EVENT_SENSITIVE",
        "observed_at": "2026-01-03T10:00:00+00:00",
        "available_at": "2026-01-03T11:00:00+00:00",
        "fetched_at": "2026-01-03T12:00:00+00:00",
        "source_version": "SANDBOX_DEMO_NON_PROD_v1",
        "quality_flags": ["DEMO_NON_PROD", "PLACEHOLDER", "SANDBOX_ONLY"],
        "payload": {
            "safe_status": "PLACEHOLDER_ONLY",
            "api_key": "DEMO_NON_PROD_FAKE_API_KEY_VALUE",
            "nested": {
                "Authorization": "Bearer DEMO_NON_PROD_FAKE_TOKEN",
                "provider_credentials": {"password": "DEMO_NON_PROD_FAKE_PASSWORD"},
            },
        },
    }
    adapter = SandboxProviderAdapter(payloads=(sensitive_placeholder_payload,))

    summaries = adapter.payload_summaries()
    serialized = json.dumps(summaries)

    assert summaries[0]["payload"]["safe_status"] == "PLACEHOLDER_ONLY"
    assert summaries[0]["payload"]["api_key"] == "[REDACTED]"
    assert summaries[0]["payload"]["nested"]["Authorization"] == "[REDACTED]"
    assert summaries[0]["payload"]["nested"]["provider_credentials"] == "[REDACTED]"
    assert "DEMO_NON_PROD_FAKE_API_KEY_VALUE" not in serialized
    assert "DEMO_NON_PROD_FAKE_TOKEN" not in serialized
    assert "DEMO_NON_PROD_FAKE_PASSWORD" not in serialized


def test_sandbox_status_endpoint_is_read_only_safe_and_sanitized() -> None:
    response = client.get("/api/v1/providers/sandbox/status")

    assert response.status_code == 200
    for header_name, header_value in SECURITY_HEADERS.items():
        assert response.headers[header_name] == header_value

    payload = response.json()
    body = response.text.lower()
    assert payload["metadata"]["phase"] == "phase-18-api-football-env-gated-smoke-client"
    assert payload["sandbox_mode"] == SANDBOX_MODE
    assert payload["provider_enabled"] is False
    assert payload["api_football_connected"] is False
    assert payload["network_calls_enabled"] is False
    assert payload["credentials_configured"] is False
    assert payload["db_ingestion_enabled"] is False
    assert payload["prediction_creation_enabled"] is False
    assert payload["production_mock_fallback_allowed"] is False
    assert payload["payload_count"] == len(SANDBOX_GOLDEN_PAYLOADS)
    assert payload["raw_hashes"] == [stable_raw_hash(golden_payload) for golden_payload in SANDBOX_GOLDEN_PAYLOADS]
    assert payload["qa_markers"] == ["DEMO_NON_PROD", "PLACEHOLDER", "SANDBOX_ONLY"]
    assert payload["onboarding_requirements"] == list(PROVIDER_ONBOARDING_REQUIREMENTS)
    assert payload["rate_limit_quota_contracts"] == list(RATE_LIMIT_QUOTA_CONTRACTS)
    assert payload["reconciliation_readiness"] == list(RECONCILIATION_READINESS_REQUIREMENTS)
    assert payload["sandbox_integration_flow"] == list(SANDBOX_INTEGRATION_FLOW)
    assert "provider_network_calls=disabled" in payload["rate_limit_quota_contracts"]
    assert "database_writes=disabled_in_phase_14" in payload["reconciliation_readiness"]
    assert payload["onboarding_gate"]["status"] == "blocked_until_real_provider_audit"
    assert payload["onboarding_gate"]["can_activate"] is False
    assert payload["secret_safety"]["configured"] is False
    assert payload["secret_safety"]["missing"] is True
    assert payload["secret_safety"]["raw_values_exposed"] is False
    assert payload["secret_safety"]["public_env_var_names_exposed"] is False
    preflight_review = payload["preflight_review"]
    assert preflight_review["status"] == "blocked_until_real_provider_preflight_approved"
    assert preflight_review["real_provider_preparation_ready"] is False
    assert preflight_review["providers_enabled"] is False
    assert preflight_review["network_calls_enabled"] is False
    assert preflight_review["db_ingestion_enabled"] is False
    assert preflight_review["blocking_reasons"] == list(PROVIDER_PREFLIGHT_BLOCKING_REASONS)
    assert preflight_review["future_checklist"] == list(PROVIDER_PREFLIGHT_FUTURE_CHECKLIST)
    assert payload["payload_summaries"]

    for secret_token in ("api_key", "password", "provider_credentials", "bearer", "authorization"):
        assert secret_token not in body

    for summary in payload["payload_summaries"]:
        assert summary["fixture_marker"] == SANDBOX_MODE
        assert "PLACEHOLDER" in json.dumps(summary)
        assert "score" not in json.dumps(summary).lower()
        assert "winner" not in json.dumps(summary).lower()


def test_sandbox_status_post_is_not_available() -> None:
    response = client.post("/api/v1/providers/sandbox/status", json={})

    assert response.status_code == 405


def test_sandbox_status_does_not_open_network_socket(monkeypatch) -> None:
    def fail_create_connection(*args: object, **kwargs: object) -> None:
        raise AssertionError("sandbox status must not open network sockets")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    response = client.get("/api/v1/providers/sandbox/status")

    assert response.status_code == 200
    assert response.json()["network_calls_enabled"] is False
