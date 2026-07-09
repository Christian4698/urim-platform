from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
FIXTURE_DATA_FRESHNESS_AUDIT_MODE: Final = (
    "fixture_data_freshness_provider_audit_trail"
)
FIXTURE_STAGING_TARGET_TABLE: Final = "api_football_fixture_staging"
DEFAULT_FRESHNESS_THRESHOLD_MINUTES: Final = 180


class ApiFootballFixtureDataFreshnessAuditValidationError(ValueError):
    """Raised when a Phase 41 freshness audit request is outside the safe contract."""


def build_fixture_data_freshness_audit(
    rows: Sequence[Mapping[str, Any]],
    *,
    now_utc: datetime,
    freshness_threshold_minutes: int = DEFAULT_FRESHNESS_THRESHOLD_MINUTES,
) -> dict[str, Any]:
    validated_now = _validate_now_utc(now_utc)
    validated_threshold = _validate_threshold_minutes(freshness_threshold_minutes)
    freshness_window = timedelta(minutes=validated_threshold)

    row_count = len(rows)
    fresh_count = 0
    stale_count = 0
    missing_fetched_at_count = 0
    invalid_fetched_at_count = 0
    payload_hash_present_count = 0
    payload_top_level_keys_present_count = 0
    provider_fixture_id_missing_count = 0
    wrong_provider_found = False
    source_modes: set[str] = set()
    fixture_status_short_counter: Counter[str] = Counter()

    for row in rows:
        if row.get("provider") != API_FOOTBALL_PROVIDER:
            wrong_provider_found = True

        if _positive_int_like(row.get("provider_fixture_id")) is None:
            provider_fixture_id_missing_count += 1

        if _has_text(row.get("payload_hash")):
            payload_hash_present_count += 1
        if _has_payload_top_level_keys(row.get("payload_top_level_keys")):
            payload_top_level_keys_present_count += 1

        if source_mode := _safe_text(row.get("source_mode")):
            source_modes.add(source_mode)
        if fixture_status_short := _safe_text(row.get("fixture_status_short")):
            fixture_status_short_counter[fixture_status_short] += 1

        fetched_at = row.get("fetched_at")
        if _is_missing_fetched_at(fetched_at):
            missing_fetched_at_count += 1
            continue

        parsed_fetched_at = _parse_fetched_at(fetched_at)
        if parsed_fetched_at is None or parsed_fetched_at > validated_now:
            invalid_fetched_at_count += 1
            continue

        if validated_now - parsed_fetched_at <= freshness_window:
            fresh_count += 1
        else:
            stale_count += 1

    payload_hash_missing_count = row_count - payload_hash_present_count
    payload_top_level_keys_missing_count = (
        row_count - payload_top_level_keys_present_count
    )
    blocking_reasons = _blocking_reasons(
        row_count=row_count,
        stale_count=stale_count,
        missing_fetched_at_count=missing_fetched_at_count,
        invalid_fetched_at_count=invalid_fetched_at_count,
        payload_hash_missing_count=payload_hash_missing_count,
        payload_top_level_keys_missing_count=payload_top_level_keys_missing_count,
        provider_fixture_id_missing_count=provider_fixture_id_missing_count,
        wrong_provider_found=wrong_provider_found,
    )

    return {
        "provider": API_FOOTBALL_PROVIDER,
        "mode": FIXTURE_DATA_FRESHNESS_AUDIT_MODE,
        "target_table": FIXTURE_STAGING_TARGET_TABLE,
        "read_only": True,
        "db_writes": False,
        "prediction_created": False,
        "betting_created": False,
        "freshness_threshold_minutes": validated_threshold,
        "row_count": row_count,
        "fresh_count": fresh_count,
        "stale_count": stale_count,
        "missing_fetched_at_count": missing_fetched_at_count,
        "invalid_fetched_at_count": invalid_fetched_at_count,
        "payload_hash_present_count": payload_hash_present_count,
        "payload_hash_missing_count": payload_hash_missing_count,
        "payload_top_level_keys_present_count": payload_top_level_keys_present_count,
        "source_modes": sorted(source_modes),
        "fixture_status_short_counts": dict(
            sorted(fixture_status_short_counter.items())
        ),
        "provider_fixture_id_missing_count": provider_fixture_id_missing_count,
        "ready_for_internal_read": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }


def _validate_now_utc(value: Any) -> datetime:
    if not isinstance(value, datetime):
        raise ApiFootballFixtureDataFreshnessAuditValidationError(
            "now_utc must be a datetime."
        )
    if value.tzinfo is None or value.tzinfo.utcoffset(value) != timedelta(0):
        raise ApiFootballFixtureDataFreshnessAuditValidationError(
            "now_utc must be timezone-aware UTC."
        )
    return value


def _validate_threshold_minutes(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ApiFootballFixtureDataFreshnessAuditValidationError(
            "freshness_threshold_minutes must be a positive integer."
        )
    return value


def _parse_fetched_at(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return None
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value:
            return None
        try:
            parsed_value = datetime.fromisoformat(
                stripped_value.removesuffix("Z") + "+00:00"
                if stripped_value.endswith("Z")
                else stripped_value
            )
        except ValueError:
            return None
        if parsed_value.tzinfo is None or parsed_value.tzinfo.utcoffset(
            parsed_value
        ) is None:
            return None
        return parsed_value.astimezone(timezone.utc)
    return None


def _is_missing_fetched_at(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_payload_top_level_keys(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(bool(str(key).strip()) for key in value)
    if isinstance(value, Sequence):
        return any(bool(str(item).strip()) for item in value)
    return False


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _positive_int_like(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str):
        stripped_value = value.strip()
        if stripped_value.isdecimal():
            parsed_value = int(stripped_value)
            return parsed_value if parsed_value > 0 else None
    return None


def _blocking_reasons(
    *,
    row_count: int,
    stale_count: int,
    missing_fetched_at_count: int,
    invalid_fetched_at_count: int,
    payload_hash_missing_count: int,
    payload_top_level_keys_missing_count: int,
    provider_fixture_id_missing_count: int,
    wrong_provider_found: bool,
) -> list[str]:
    reasons: list[str] = []
    if row_count == 0:
        reasons.append("no_rows")
    if wrong_provider_found:
        reasons.append("wrong_provider")
    if stale_count > 0:
        reasons.append("stale_rows")
    if missing_fetched_at_count > 0:
        reasons.append("missing_fetched_at")
    if invalid_fetched_at_count > 0:
        reasons.append("invalid_fetched_at")
    if payload_hash_missing_count > 0:
        reasons.append("payload_hash_missing")
    if payload_top_level_keys_missing_count > 0:
        reasons.append("payload_top_level_keys_missing")
    if provider_fixture_id_missing_count > 0:
        reasons.append("provider_fixture_id_missing")
    return reasons


__all__ = [
    "API_FOOTBALL_PROVIDER",
    "ApiFootballFixtureDataFreshnessAuditValidationError",
    "DEFAULT_FRESHNESS_THRESHOLD_MINUTES",
    "FIXTURE_DATA_FRESHNESS_AUDIT_MODE",
    "FIXTURE_STAGING_TARGET_TABLE",
    "build_fixture_data_freshness_audit",
]
