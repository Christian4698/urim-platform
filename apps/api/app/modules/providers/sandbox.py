from datetime import datetime
import hashlib
import json
from typing import Any

from app.modules.providers.quality import (
    assert_network_calls_disabled,
    assert_no_production_mock_fallback,
    build_quality_report,
    sanitize_provider_payload,
)
from app.modules.providers.secret_safety import build_provider_secret_safety_summary
from app.schemas.common import build_metadata
from app.schemas.providers import (
    CanonicalEntityMapping,
    DataQualityReport,
    OfficialResultEnvelope,
    ProviderCapability,
    ProviderCapabilityMatrix,
    ProviderIdentity,
    ProviderObservation,
    RawPayloadReference,
    SandboxProviderStatusResponse,
    TemporalAvailabilityMetadata,
    disabled_provider_capabilities,
)

SANDBOX_PROVIDER_ID = "sandbox-provider-demo-non-prod"
SANDBOX_MODE = "DEMO_NON_PROD"
SANDBOX_SOURCE_VERSION = "SANDBOX_DEMO_NON_PROD_v1"

SANDBOX_GOLDEN_PAYLOADS: tuple[dict[str, Any], ...] = (
    {
        "fixture_marker": "DEMO_NON_PROD",
        "provider": SANDBOX_PROVIDER_ID,
        "provider_event_id": "PLACEHOLDER_SANDBOX_EVENT_001",
        "observed_at": "2026-01-01T10:00:00+00:00",
        "available_at": "2026-01-01T11:00:00+00:00",
        "fetched_at": "2026-01-01T12:00:00+00:00",
        "source_version": SANDBOX_SOURCE_VERSION,
        "quality_flags": ["DEMO_NON_PROD", "PLACEHOLDER", "SANDBOX_ONLY"],
        "payload": {
            "competition_label": "PLACEHOLDER_COMPETITION",
            "home_entity_label": "PLACEHOLDER_HOME_ENTITY_A",
            "away_entity_label": "PLACEHOLDER_AWAY_ENTITY_B",
            "status": "PLACEHOLDER_ONLY",
            "data_state": "PLACEHOLDER_NO_OFFICIAL_DATA",
        },
    },
    {
        "fixture_marker": "DEMO_NON_PROD",
        "provider": SANDBOX_PROVIDER_ID,
        "provider_event_id": "PLACEHOLDER_SANDBOX_EVENT_002",
        "observed_at": "2026-01-02T10:00:00+00:00",
        "available_at": "2026-01-02T11:00:00+00:00",
        "fetched_at": "2026-01-02T12:00:00+00:00",
        "source_version": SANDBOX_SOURCE_VERSION,
        "quality_flags": ["DEMO_NON_PROD", "PLACEHOLDER", "SANDBOX_ONLY"],
        "payload": {
            "competition_label": "PLACEHOLDER_COMPETITION",
            "home_entity_label": "PLACEHOLDER_HOME_ENTITY_C",
            "away_entity_label": "PLACEHOLDER_AWAY_ENTITY_D",
            "status": "PLACEHOLDER_ONLY",
            "data_state": "PLACEHOLDER_NO_OFFICIAL_DATA",
        },
    },
)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_raw_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _parse_aware_datetime(value: str) -> datetime:
    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None:
        raise ValueError("sandbox timestamps must be timezone-aware")
    return timestamp


class SandboxProviderAdapter:
    """In-memory, non-production adapter for contract validation only."""

    def __init__(self, payloads: tuple[dict[str, Any], ...] = SANDBOX_GOLDEN_PAYLOADS) -> None:
        self._payloads = payloads

    def identity(self) -> ProviderIdentity:
        provider = ProviderIdentity(
            provider=SANDBOX_PROVIDER_ID,
            display_name="Sandbox Provider DEMO_NON_PROD",
        )
        assert_no_production_mock_fallback(provider)
        assert_network_calls_disabled(provider)
        return provider

    def health(self) -> dict[str, Any]:
        return {
            "status": "sandbox_ready_non_prod",
            "sandbox_mode": SANDBOX_MODE,
            "network_calls_enabled": False,
            "credentials_configured": False,
            "db_ingestion_enabled": False,
            "prediction_creation_enabled": False,
        }

    def capabilities(self) -> list[ProviderCapability]:
        return disabled_provider_capabilities()

    def capability_matrix(self) -> ProviderCapabilityMatrix:
        return ProviderCapabilityMatrix()

    def coverage(self) -> dict[str, Any]:
        return {
            "sandbox_mode": SANDBOX_MODE,
            "coverage_status": "PLACEHOLDER_ONLY",
            "real_sports_coverage": False,
            "payload_count": len(self._payloads),
        }

    def fetch_competitions(self) -> list[ProviderObservation]:
        return []

    def fetch_fixtures(self, window: dict[str, datetime]) -> list[ProviderObservation]:
        _ = window
        return [self._observation_from_payload(payload) for payload in self._payloads]

    def fetch_fixture(self, fixture_id: str) -> ProviderObservation:
        for payload in self._payloads:
            if payload["provider_event_id"] == fixture_id:
                return self._observation_from_payload(payload)
        raise KeyError(f"sandbox fixture not found: {fixture_id}")

    def fetch_lineups(self, fixture_id: str) -> list[ProviderObservation]:
        _ = fixture_id
        return []

    def fetch_injuries(self, scope: dict[str, Any]) -> list[ProviderObservation]:
        _ = scope
        return []

    def fetch_statistics(self, fixture_id: str) -> list[ProviderObservation]:
        _ = fixture_id
        return []

    def fetch_live_events(self, fixture_id: str, cursor: str | None = None) -> list[ProviderObservation]:
        _ = (fixture_id, cursor)
        return []

    def fetch_odds(self, event_id: str, market: str, as_of: datetime) -> list[ProviderObservation]:
        _ = (event_id, market, as_of)
        return []

    def normalize(self, raw_payload: RawPayloadReference) -> ProviderObservation:
        for payload in self._payloads:
            if stable_raw_hash(payload) == raw_payload.raw_hash:
                return self._observation_from_payload(payload)
        raise KeyError(f"sandbox payload not found for hash: {raw_payload.raw_hash}")

    def map_entity(self, observation: ProviderObservation) -> CanonicalEntityMapping:
        return CanonicalEntityMapping(
            provider=observation.provider,
            provider_entity_id=observation.provider_event_id,
            provider_entity_type="sandbox_fixture",
            canonical_entity_id=None,
            valid_from=observation.available_at,
            confidence=0.0,
            quality_flags=[*observation.quality_flags, "NO_CANONICAL_MAPPING"],
        )

    def temporal_metadata(self, observation: ProviderObservation) -> TemporalAvailabilityMetadata:
        return TemporalAvailabilityMetadata(
            provider=observation.provider,
            provider_event_id=observation.provider_event_id,
            observed_at=observation.observed_at,
            available_at=observation.available_at,
            fetched_at=observation.fetched_at,
            source_version=observation.source_version,
            raw_hash=observation.raw_hash,
            quality_flags=list(observation.quality_flags),
        )

    def quality_report(self, observation: ProviderObservation) -> DataQualityReport:
        return build_quality_report(observation)

    def official_result_envelope(self, observation: ProviderObservation) -> OfficialResultEnvelope:
        """Build a sandbox-only placeholder envelope; this is not a real result verifier."""
        return OfficialResultEnvelope(
            provider=observation.provider,
            provider_event_id=observation.provider_event_id,
            observed_at=observation.observed_at,
            available_at=observation.available_at,
            fetched_at=observation.fetched_at,
            source_version=observation.source_version,
            raw_hash=observation.raw_hash,
            quality_flags=[*observation.quality_flags, "NO_OFFICIAL_DATA"],
            result_payload={
                "fixture_marker": SANDBOX_MODE,
                "data_state": "PLACEHOLDER_NO_OFFICIAL_DATA",
            },
        )

    def raw_hashes(self) -> list[str]:
        return [stable_raw_hash(payload) for payload in self._payloads]

    def payload_summaries(self) -> list[dict[str, Any]]:
        return [
            sanitize_provider_payload(
                {
                    "fixture_marker": payload["fixture_marker"],
                    "provider": payload["provider"],
                    "provider_event_id": payload["provider_event_id"],
                    "source_version": payload["source_version"],
                    "raw_hash": stable_raw_hash(payload),
                    "quality_flags": list(payload["quality_flags"]),
                    "payload": payload["payload"],
                }
            )
            for payload in self._payloads
        ]

    def _raw_payload_reference(self, payload: dict[str, Any]) -> RawPayloadReference:
        return RawPayloadReference(
            provider=payload["provider"],
            provider_event_id=payload["provider_event_id"],
            fetched_at=_parse_aware_datetime(payload["fetched_at"]),
            source_version=payload["source_version"],
            raw_hash=stable_raw_hash(payload),
            endpoint="sandbox://in-memory",
            metadata={
                "fixture_marker": payload["fixture_marker"],
                "sandbox_mode": SANDBOX_MODE,
                "payload_location": "in_memory_sandbox",
            },
        )

    def _observation_from_payload(self, payload: dict[str, Any]) -> ProviderObservation:
        raw_payload_ref = self._raw_payload_reference(payload)
        return ProviderObservation(
            provider=payload["provider"],
            provider_event_id=payload["provider_event_id"],
            observed_at=_parse_aware_datetime(payload["observed_at"]),
            available_at=_parse_aware_datetime(payload["available_at"]),
            fetched_at=_parse_aware_datetime(payload["fetched_at"]),
            source_version=payload["source_version"],
            raw_hash=raw_payload_ref.raw_hash,
            quality_flags=list(payload["quality_flags"]),
            raw_payload_ref=raw_payload_ref,
            data=sanitize_provider_payload(payload["payload"]),
        )


def get_sandbox_provider_adapter() -> SandboxProviderAdapter:
    return SandboxProviderAdapter()


def build_sandbox_provider_status_response() -> SandboxProviderStatusResponse:
    adapter = get_sandbox_provider_adapter()
    identity = adapter.identity()
    return SandboxProviderStatusResponse(
        metadata=build_metadata(),
        provider_identity=identity,
        payload_count=len(SANDBOX_GOLDEN_PAYLOADS),
        raw_hashes=adapter.raw_hashes(),
        capabilities=adapter.capabilities(),
        secret_safety=build_provider_secret_safety_summary(),
        payload_summaries=adapter.payload_summaries(),
        safeguards=[
            "Sandbox adapter is DEMO_NON_PROD and informational only.",
            "Sandbox adapter reads only in-memory PLACEHOLDER payloads.",
            "No provider network calls, credentials, DB ingestion or prediction creation are enabled.",
            "Provider onboarding gate blocks real provider activation in Phase 12.",
            "Rate-limit, quota, reconciliation and secret safety contracts are readiness-only in Phase 12.",
            "Official result envelope output is a sandbox placeholder, not activated Post-Match Learning.",
            "Public sandbox payload summaries are sanitized before exposure.",
        ],
    )
