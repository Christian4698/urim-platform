from datetime import datetime
from typing import Any

from app.schemas.providers import (
    DataQualityReport,
    ProviderIdentity,
    ProviderObservation,
    REQUIRED_PROVENANCE_FIELDS,
    TemporalAvailabilityMetadata,
)


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


def build_quality_report(observation: ProviderObservation) -> DataQualityReport:
    validate_required_provenance_fields(observation.model_dump())
    return DataQualityReport(
        quality_flags=list(observation.quality_flags),
        temporal_order_valid=True,
        complete_provenance=True,
    )
