from datetime import datetime
from typing import Any

from app.schemas.providers import (
    DataQualityReport,
    ProviderIdentity,
    ProviderObservation,
    REQUIRED_PROVENANCE_FIELDS,
    TemporalAvailabilityMetadata,
)

REDACTED_VALUE = "[REDACTED]"
SENSITIVE_PAYLOAD_KEY_PARTS = (
    "api_key",
    "token",
    "authorization",
    "secret",
    "password",
    "bearer",
    "credential",
    "provider_credentials",
)


def _is_sensitive_key(key: object) -> bool:
    normalized_key = str(key).lower()
    return any(sensitive_part in normalized_key for sensitive_part in SENSITIVE_PAYLOAD_KEY_PARTS)


def validate_required_provenance_fields(payload: dict[str, Any]) -> None:
    missing_fields = [field for field in REQUIRED_PROVENANCE_FIELDS if field not in payload]
    if missing_fields:
        raise ValueError(f"missing provider provenance fields: {', '.join(missing_fields)}")

    empty_fields = [
        field
        for field in ("provider", "provider_event_id", "source_version", "raw_hash")
        if not payload.get(field)
    ]
    if empty_fields:
        raise ValueError(f"empty provider provenance fields: {', '.join(empty_fields)}")

    quality_flags = payload.get("quality_flags")
    if not isinstance(quality_flags, list):
        raise ValueError("quality_flags must be present as a list")


def assert_provider_timestamps_aware(metadata: TemporalAvailabilityMetadata) -> None:
    for field_name in ("observed_at", "available_at", "fetched_at"):
        timestamp = getattr(metadata, field_name)
        if timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None:
            raise ValueError(f"{field_name} must be timezone-aware")


def is_temporal_order_valid(metadata: TemporalAvailabilityMetadata) -> bool:
    return metadata.observed_at <= metadata.available_at <= metadata.fetched_at


def assert_available_before_prediction_time(
    metadata: TemporalAvailabilityMetadata,
    prediction_time: datetime,
) -> None:
    if prediction_time.tzinfo is None or prediction_time.tzinfo.utcoffset(prediction_time) is None:
        raise ValueError("prediction_time must be timezone-aware")

    if metadata.available_at > prediction_time:
        raise ValueError("available_at must be less than or equal to prediction_time")


def assert_no_production_mock_fallback(provider: ProviderIdentity) -> None:
    if provider.production_mock_fallback_allowed is not False:
        raise ValueError("production mock fallback must remain disabled")


def assert_network_calls_disabled(provider: ProviderIdentity) -> None:
    if provider.network_calls_enabled is not False:
        raise ValueError("provider network calls must remain disabled")


def sanitize_provider_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {
            key: REDACTED_VALUE if _is_sensitive_key(key) else sanitize_provider_payload(value)
            for key, value in payload.items()
        }

    if isinstance(payload, list):
        return [sanitize_provider_payload(item) for item in payload]

    return payload


def build_quality_report(observation: ProviderObservation) -> DataQualityReport:
    validate_required_provenance_fields(observation.model_dump())
    assert_provider_timestamps_aware(observation)
    return DataQualityReport(
        quality_flags=list(observation.quality_flags),
        temporal_order_valid=is_temporal_order_valid(observation),
        complete_provenance=True,
    )
