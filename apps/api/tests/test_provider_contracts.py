from datetime import UTC, datetime, timedelta
import json
import socket

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.security import SECURITY_HEADERS
from app.main import app
from app.modules.providers.api_football_smoke_client import API_FOOTBALL_SMOKE_ENV_NAMES
from app.modules.providers.quality import (
    assert_available_before_prediction_time,
    assert_network_calls_disabled,
    assert_no_production_mock_fallback,
    build_quality_report,
    is_temporal_order_valid,
    sanitize_provider_payload,
    validate_required_provenance_fields,
)
from app.schemas.providers import (
    API_FOOTBALL_TEST_RESPONSE_CONTRACTS,
    DISALLOWED_LEARNING_SOURCES,
    POST_MATCH_LEARNING_SOURCE,
    PROVIDER_ONBOARDING_REQUIREMENTS,
    PROVIDER_PREFLIGHT_BLOCKING_REASONS,
    PROVIDER_PREFLIGHT_FUTURE_CHECKLIST,
    PROVIDER_QA_REQUIREMENTS,
    RATE_LIMIT_QUOTA_CONTRACTS,
    RECONCILIATION_READINESS_REQUIREMENTS,
    CanonicalEntityMapping,
    OfficialResultEnvelope,
    ProviderCapabilityMatrix,
    ProviderIdentity,
    ProviderObservation,
    RawPayloadReference,
    TemporalAvailabilityMetadata,
)
from tests.fixtures.provider_golden_payloads import GOLDEN_PAYLOADS
from tests.helpers.payload_helpers import walk_keys, walk_values

client = TestClient(app)


def aware_time(hour: int) -> datetime:
    return datetime(2026, 1, 1, hour, 0, tzinfo=UTC)


def complete_provenance_payload() -> dict[str, object]:
    return {
        "provider": "contract-test-provider",
        "provider_event_id": "provider-event-001",
        "observed_at": aware_time(10),
        "available_at": aware_time(11),
        "fetched_at": aware_time(12),
        "source_version": "contract-v1",
        "raw_hash": "raw-hash-001",
        "quality_flags": ["contract_only"],
    }


def test_provider_observation_accepts_complete_provenance() -> None:
    raw_payload_ref = RawPayloadReference(
        provider="contract-test-provider",
        provider_event_id="provider-event-001",
        fetched_at=aware_time(12),
        source_version="contract-v1",
        raw_hash="raw-hash-001",
    )

    observation = ProviderObservation(
        **complete_provenance_payload(),
        raw_payload_ref=raw_payload_ref,
        data={"status": "contract_only"},
    )

    quality_report = build_quality_report(observation)

    assert quality_report.complete_provenance is True
    assert quality_report.temporal_order_valid is True
    assert quality_report.providers_enabled is False
    assert quality_report.network_calls_enabled is False
    assert quality_report.production_mock_fallback_allowed is False


def test_missing_provider_provenance_is_rejected() -> None:
    payload = complete_provenance_payload()
    payload.pop("raw_hash")

    with pytest.raises(ValidationError):
        ProviderObservation(**payload)

    with pytest.raises(ValueError, match="missing provider provenance fields: raw_hash"):
        validate_required_provenance_fields(payload)


def test_empty_required_provider_provenance_is_rejected() -> None:
    payload = complete_provenance_payload()
    payload["provider_event_id"] = ""

    with pytest.raises(ValidationError):
        ProviderObservation(**payload)

    with pytest.raises(ValueError, match="empty provider provenance fields: provider_event_id"):
        validate_required_provenance_fields(payload)


def test_naive_provider_timestamps_are_rejected() -> None:
    payload = complete_provenance_payload()
    payload["observed_at"] = datetime(2026, 1, 1, 10, 0)

    with pytest.raises(ValidationError, match="provider timestamps must be timezone-aware"):
        ProviderObservation(**payload)


def test_invalid_provider_temporal_order_is_rejected() -> None:
    payload = complete_provenance_payload()
    payload["available_at"] = aware_time(13)

    with pytest.raises(
        ValidationError,
        match="provider timestamps must satisfy observed_at <= available_at <= fetched_at",
    ):
        ProviderObservation(**payload)


def test_available_after_prediction_time_is_rejected() -> None:
    metadata = TemporalAvailabilityMetadata(**complete_provenance_payload())

    with pytest.raises(ValueError, match="available_at must be less than or equal to prediction_time"):
        assert_available_before_prediction_time(metadata, aware_time(10))

    assert_available_before_prediction_time(metadata, aware_time(11))


def test_provider_capability_matrix_remains_fully_disabled() -> None:
    capability_matrix = ProviderCapabilityMatrix()

    for capability in capability_matrix.as_list():
        assert capability.enabled is False
        assert capability.status == "disabled"


def test_provider_identity_rejects_production_mock_fallback() -> None:
    with pytest.raises(ValidationError):
        ProviderIdentity(
            provider="contract-test-provider",
            display_name="Contract Test Provider",
            production_mock_fallback_allowed=True,
        )


def test_production_mock_fallback_helper_rejects_bypassed_model() -> None:
    provider = ProviderIdentity.model_construct(
        provider="contract-test-provider",
        display_name="Contract Test Provider",
        production_mock_fallback_allowed=True,
    )

    with pytest.raises(ValueError, match="production mock fallback must remain disabled"):
        assert_no_production_mock_fallback(provider)


def test_network_calls_disabled_helper_rejects_bypassed_model() -> None:
    provider = ProviderIdentity.model_construct(
        provider="contract-test-provider",
        display_name="Contract Test Provider",
        network_calls_enabled=True,
    )

    with pytest.raises(ValueError, match="provider network calls must remain disabled"):
        assert_network_calls_disabled(provider)


def test_canonical_entity_mapping_keeps_valid_temporal_window() -> None:
    mapping = CanonicalEntityMapping(
        provider="contract-test-provider",
        provider_entity_id="team-001",
        provider_entity_type="team",
        canonical_entity_id="canonical-team-001",
        valid_from=aware_time(10),
        valid_to=aware_time(12),
        confidence=0.9,
        quality_flags=["contract_only"],
    )

    assert mapping.canonical_entity_id == "canonical-team-001"

    with pytest.raises(ValidationError, match="valid_to must be greater than or equal to valid_from"):
        CanonicalEntityMapping(
            provider="contract-test-provider",
            provider_entity_id="team-001",
            provider_entity_type="team",
            valid_from=aware_time(12),
            valid_to=aware_time(10),
            confidence=0.9,
            quality_flags=["contract_only"],
        )


def test_official_result_learning_source_is_restricted() -> None:
    envelope = OfficialResultEnvelope(
        **complete_provenance_payload(),
        result_payload={"status": "contract_only"},
    )

    assert envelope.learning_source == POST_MATCH_LEARNING_SOURCE
    assert envelope.disallowed_learning_sources == list(DISALLOWED_LEARNING_SOURCES)

    with pytest.raises(ValidationError, match="official result learning source must be post_match_outcomes_only"):
        OfficialResultEnvelope(
            **complete_provenance_payload(),
            learning_source="tickets.user_declared_result",
        )


def test_provider_readiness_endpoint_is_read_only_and_contract_only() -> None:
    response = client.get("/api/v1/providers/readiness")

    assert response.status_code == 200
    for header_name, header_value in SECURITY_HEADERS.items():
        assert response.headers[header_name] == header_value

    payload = response.json()
    assert payload["metadata"]["phase"] == "phase-19-api-football-manual-smoke-runner"
    assert payload["providers_enabled"] is False
    assert payload["api_football_connected"] is False
    assert payload["network_calls_enabled"] is False
    assert payload["credentials_configured"] is False
    assert payload["quality_report"]["production_mock_fallback_allowed"] is False
    assert payload["qa_requirements"] == list(PROVIDER_QA_REQUIREMENTS)
    assert payload["qa_requirements_description"]
    assert payload["onboarding_requirements"] == list(PROVIDER_ONBOARDING_REQUIREMENTS)
    assert payload["onboarding_requirements_description"]
    assert payload["rate_limit_quota_contracts"] == list(RATE_LIMIT_QUOTA_CONTRACTS)
    assert payload["reconciliation_readiness"] == list(RECONCILIATION_READINESS_REQUIREMENTS)
    assert "provider_network_calls=disabled" in payload["rate_limit_quota_contracts"]
    assert "database_writes=disabled_in_phase_14" in payload["reconciliation_readiness"]
    assert payload["onboarding_gate"]["status"] == "blocked_until_real_provider_audit"
    assert payload["onboarding_gate"]["can_activate"] is False
    assert payload["onboarding_gate"]["providers_enabled"] is False
    assert payload["secret_safety"]["configured"] is False
    assert payload["secret_safety"]["missing"] is True
    assert payload["secret_safety"]["providers_enabled"] is False
    assert payload["secret_safety"]["activation_allowed"] is False
    assert payload["secret_safety"]["raw_values_exposed"] is False
    assert payload["secret_safety"]["public_env_var_names_exposed"] is False
    preflight_review = payload["preflight_review"]
    assert preflight_review["status"] == "blocked_until_real_provider_preflight_approved"
    assert preflight_review["real_provider_preparation_ready"] is False
    assert preflight_review["providers_enabled"] is False
    assert preflight_review["network_calls_enabled"] is False
    assert preflight_review["credentials_configured"] is False
    assert preflight_review["db_ingestion_enabled"] is False
    assert preflight_review["api_football_connected"] is False
    assert preflight_review["blocking_reasons"] == list(PROVIDER_PREFLIGHT_BLOCKING_REASONS)
    assert preflight_review["future_checklist"] == list(PROVIDER_PREFLIGHT_FUTURE_CHECKLIST)
    assert preflight_review["decision"] == "blocked"
    shell_status = payload["real_provider_shell_status"]
    assert shell_status["label"] == "api_football_future_provider_shell"
    assert shell_status["status"] == "blocked_shell_only"
    assert shell_status["provider_enabled"] is False
    assert shell_status["providers_enabled"] is False
    assert shell_status["api_football_connected"] is False
    assert shell_status["network_calls_enabled"] is False
    assert shell_status["credentials_configured"] is False
    assert shell_status["http_client_enabled"] is False
    assert shell_status["provider_base_url_configured"] is False
    assert shell_status["provider_endpoint_configured"] is False
    assert shell_status["real_requests_enabled"] is False
    assert shell_status["db_ingestion_enabled"] is False
    assert shell_status["prediction_creation_enabled"] is False
    assert shell_status["production_payloads_enabled"] is False
    final_gate = payload["activation_readiness_final_gate"]
    assert final_gate["status"] == "blocked_until_provider_activation_final_gate_approved"
    assert final_gate["can_activate_provider"] is False
    assert final_gate["providers_enabled"] is False
    assert final_gate["api_football_connected"] is False
    assert final_gate["network_calls_enabled"] is False
    assert final_gate["db_ingestion_enabled"] is False
    assert final_gate["credentials_accepted"] is False
    assert final_gate["production_provider_allowed"] is False
    assert final_gate["decision"] == "blocked"
    api_football_adapter_status = payload["api_football_read_only_adapter_status"]
    assert api_football_adapter_status["status"] == "disabled_until_provider_activation_gate_approved"
    assert api_football_adapter_status["enabled"] is False
    assert api_football_adapter_status["connected"] is False
    assert api_football_adapter_status["network_calls_enabled"] is False
    assert api_football_adapter_status["db_ingestion_enabled"] is False
    assert api_football_adapter_status["credentials_loaded"] is False
    assert api_football_adapter_status["prediction_creation_enabled"] is False
    assert api_football_adapter_status["betting_enabled"] is False
    test_transport_status = payload["api_football_test_transport_contracts_status"]
    assert test_transport_status["status"] == "test_only_contracts_no_public_runtime"
    assert test_transport_status["test_transport_enabled"] is False
    assert test_transport_status["public_endpoint_enabled"] is False
    assert test_transport_status["network_calls_enabled"] is False
    assert test_transport_status["db_ingestion_enabled"] is False
    assert test_transport_status["credentials_loaded"] is False
    assert test_transport_status["prediction_creation_enabled"] is False
    assert test_transport_status["betting_enabled"] is False
    assert test_transport_status["production_payloads_enabled"] is False
    assert test_transport_status["real_provider_connected"] is False
    assert test_transport_status["response_contracts"] == list(API_FOOTBALL_TEST_RESPONSE_CONTRACTS)
    assert test_transport_status["required_markers"] == ["TEST_ONLY", "DEMO_NON_PROD", "PLACEHOLDER"]
    smoke_client_status = payload["api_football_smoke_client_status"]
    assert smoke_client_status["status"] == "disabled_until_explicit_local_smoke_env"
    assert smoke_client_status["enabled_by_default"] is False
    assert smoke_client_status["smoke_mode_enabled"] is False
    assert smoke_client_status["network_calls_enabled_by_default"] is False
    assert smoke_client_status["public_endpoint_enabled"] is False
    assert smoke_client_status["db_ingestion_enabled"] is False
    assert smoke_client_status["credentials_exposed"] is False
    assert smoke_client_status["prediction_creation_enabled"] is False
    assert smoke_client_status["betting_enabled"] is False
    assert smoke_client_status["real_provider_connected"] is False
    assert payload["post_match_learning_source"] == POST_MATCH_LEARNING_SOURCE
    assert "tickets.user_declared_profit_loss" in payload["disallowed_learning_sources"]
    assert payload["required_provenance_fields"] == [
        "provider",
        "provider_event_id",
        "observed_at",
        "available_at",
        "fetched_at",
        "source_version",
        "raw_hash",
        "quality_flags",
    ]
    assert payload["temporal_contract"] == [
        "observed_at <= available_at <= fetched_at",
        "available_at <= prediction_time",
    ]

    for capability in payload["capabilities"]:
        assert capability["enabled"] is False
        assert capability["status"] == "disabled"

    for capability in payload["capability_matrix"].values():
        assert capability["enabled"] is False
        assert capability["status"] == "disabled"


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_provider_readiness_dangerous_methods_are_not_available(method: str) -> None:
    response = client.request(method.upper(), "/api/v1/providers/readiness", json={})

    assert response.status_code == 405


def test_provider_readiness_does_not_open_network_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_create_connection(*args: object, **kwargs: object) -> None:
        raise AssertionError("provider readiness must not open network sockets")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    response = client.get("/api/v1/providers/readiness")

    assert response.status_code == 200
    assert response.json()["network_calls_enabled"] is False


def test_provider_readiness_api_football_adapter_status_is_public_safe() -> None:
    response = client.get("/api/v1/providers/readiness")

    assert response.status_code == 200
    payload = response.json()
    serialized = json.dumps(payload, sort_keys=True).lower()
    adapter_status = payload["api_football_read_only_adapter_status"]
    test_transport_status = payload["api_football_test_transport_contracts_status"]
    smoke_client_status = payload["api_football_smoke_client_status"]

    assert adapter_status["enabled"] is False
    assert adapter_status["connected"] is False
    assert adapter_status["network_calls_enabled"] is False
    assert adapter_status["db_ingestion_enabled"] is False
    assert adapter_status["credentials_loaded"] is False
    assert adapter_status["prediction_creation_enabled"] is False
    assert adapter_status["betting_enabled"] is False
    assert test_transport_status["test_transport_enabled"] is False
    assert test_transport_status["public_endpoint_enabled"] is False
    assert test_transport_status["network_calls_enabled"] is False
    assert test_transport_status["db_ingestion_enabled"] is False
    assert test_transport_status["credentials_loaded"] is False
    assert test_transport_status["prediction_creation_enabled"] is False
    assert test_transport_status["betting_enabled"] is False
    assert smoke_client_status["enabled_by_default"] is False
    assert smoke_client_status["smoke_mode_enabled"] is False
    assert smoke_client_status["network_calls_enabled_by_default"] is False
    assert smoke_client_status["db_ingestion_enabled"] is False
    assert smoke_client_status["credentials_exposed"] is False
    assert smoke_client_status["prediction_creation_enabled"] is False
    assert smoke_client_status["betting_enabled"] is False

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
        "demo_non_prod_fake_phase18_auth_material",
        "example.invalid",
        "bookmaker",
        "winner",
        "home_score",
        "away_score",
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized
    for env_name in API_FOOTBALL_SMOKE_ENV_NAMES:
        assert env_name.lower() not in serialized


def test_prediction_time_must_be_timezone_aware() -> None:
    metadata = TemporalAvailabilityMetadata(**complete_provenance_payload())

    with pytest.raises(ValueError, match="prediction_time must be timezone-aware"):
        assert_available_before_prediction_time(metadata, datetime(2026, 1, 1, 12, 0))


def test_available_before_prediction_accepts_later_prediction_time() -> None:
    metadata = TemporalAvailabilityMetadata(**complete_provenance_payload())

    assert_available_before_prediction_time(metadata, metadata.available_at + timedelta(minutes=1))


def test_quality_report_calculates_temporal_order_dynamically() -> None:
    payload = complete_provenance_payload()
    payload["observed_at"] = aware_time(12)
    payload["available_at"] = aware_time(11)
    payload["fetched_at"] = aware_time(10)
    observation = ProviderObservation.model_construct(**payload)

    assert is_temporal_order_valid(observation) is False
    assert build_quality_report(observation).temporal_order_valid is False


def test_sanitize_provider_payload_masks_sensitive_keys_recursively() -> None:
    raw_payload = {
        "api_key": "demo-api-key-value",
        "safe_name": "PLACEHOLDER_TEAM",
        "nested": {
            "Authorization": "Bearer demo-token-value",
            "safe_status": "PLACEHOLDER_ONLY",
            "provider_credentials": {"password": "demo-password-value"},
        },
        "items": [
            {"token": "demo-token-value"},
            {"bearer_header": "demo-bearer-value", "safe_value": 42},
        ],
    }

    sanitized = sanitize_provider_payload(raw_payload)
    serialized = json.dumps(sanitized)

    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["safe_name"] == "PLACEHOLDER_TEAM"
    assert sanitized["nested"]["Authorization"] == "[REDACTED]"
    assert sanitized["nested"]["safe_status"] == "PLACEHOLDER_ONLY"
    assert sanitized["nested"]["provider_credentials"] == "[REDACTED]"
    assert sanitized["items"][0]["token"] == "[REDACTED]"
    assert sanitized["items"][1]["bearer_header"] == "[REDACTED]"
    assert sanitized["items"][1]["safe_value"] == 42
    assert "demo-api-key-value" not in serialized
    assert "demo-token-value" not in serialized
    assert "demo-password-value" not in serialized
    assert "demo-bearer-value" not in serialized


def test_golden_payloads_are_demo_only_and_not_production_results() -> None:
    forbidden_result_keys = {"score", "scores", "result", "winner", "home_score", "away_score"}
    forbidden_real_names = {"Manchester", "Real Madrid", "Barcelona", "PSG", "Liverpool"}

    assert GOLDEN_PAYLOADS
    for payload in GOLDEN_PAYLOADS:
        assert payload["fixture_marker"] == "DEMO_NON_PROD"
        assert "PLACEHOLDER" in json.dumps(payload)
        assert forbidden_result_keys.isdisjoint(set(walk_keys(payload)))
        for value in walk_values(payload):
            if isinstance(value, str):
                assert not any(real_name in value for real_name in forbidden_real_names)
