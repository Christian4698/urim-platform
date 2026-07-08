from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
FIXTURE_STAGING_TARGET_TABLE: Final = "api_football_fixture_staging"
FIXTURE_STAGING_GATE_MODE: Final = "fixture_staging_ingestion_gate_only"

REQUIRED_FIXTURE_STAGING_FIELDS: Final = (
    "provider",
    "provider_fixture_id",
    "provider_league_id",
    "provider_season",
    "fixture_date",
    "fixture_timezone",
    "fixture_status_short",
    "fixture_status_long",
    "home_team_provider_id",
    "home_team_name",
    "away_team_provider_id",
    "away_team_name",
)
NUMERIC_FIXTURE_STAGING_FIELDS: Final = frozenset(
    {
        "provider_fixture_id",
        "provider_league_id",
        "provider_season",
        "home_team_provider_id",
        "away_team_provider_id",
    }
)
FORBIDDEN_FIXTURE_STAGING_FIELDS: Final = frozenset(
    {"odds", "bookmaker", "stake", "prediction", "betting"}
)


def build_fixture_staging_ingestion_gate(
    normalized_fixtures: Sequence[Mapping[str, Any]],
    *,
    payload_hash: str,
    payload_top_level_keys: Sequence[str],
    source_mode: str,
) -> dict[str, Any]:
    source_mode_value = _safe_text(source_mode)
    payload_hash_present = bool(_safe_text(payload_hash))
    payload_top_level_keys_present = _has_payload_top_level_keys(
        payload_top_level_keys
    )
    candidate_count = len(normalized_fixtures)
    duplicate_provider_fixture_ids = _duplicate_provider_fixture_ids(
        normalized_fixtures
    )
    duplicate_provider_fixture_id_set = set(duplicate_provider_fixture_ids)

    accepted_count = 0
    rejected_count = 0
    missing_required_fields: dict[str, list[str]] = {}
    wrong_provider_found = False
    forbidden_fixture_fields_found = False

    for index, fixture in enumerate(normalized_fixtures):
        missing_fields = _missing_required_fields(fixture)
        fixture_id = _positive_int_like(fixture.get("provider_fixture_id"))
        wrong_provider = fixture.get("provider") != API_FOOTBALL_PROVIDER
        duplicated = (
            fixture_id is not None
            and fixture_id in duplicate_provider_fixture_id_set
        )
        forbidden_fields = _present_forbidden_fixture_fields(fixture)

        if missing_fields:
            missing_required_fields[_candidate_reference(index, fixture)] = (
                missing_fields
            )
        if wrong_provider:
            wrong_provider_found = True
        if forbidden_fields:
            forbidden_fixture_fields_found = True

        if wrong_provider or missing_fields or duplicated or forbidden_fields:
            rejected_count += 1
        else:
            accepted_count += 1

    blocking_reasons = _blocking_reasons(
        candidate_count=candidate_count,
        source_mode_present=bool(source_mode_value),
        payload_hash_present=payload_hash_present,
        payload_top_level_keys_present=payload_top_level_keys_present,
        wrong_provider_found=wrong_provider_found,
        missing_required_fields_found=bool(missing_required_fields),
        duplicate_provider_fixture_ids_found=bool(duplicate_provider_fixture_ids),
        forbidden_fixture_fields_found=forbidden_fixture_fields_found,
    )

    return {
        "provider": API_FOOTBALL_PROVIDER,
        "target_table": FIXTURE_STAGING_TARGET_TABLE,
        "mode": FIXTURE_STAGING_GATE_MODE,
        "db_writes": False,
        "prediction_created": False,
        "betting_created": False,
        "source_mode": source_mode_value,
        "payload_hash_present": payload_hash_present,
        "payload_top_level_keys_present": payload_top_level_keys_present,
        "candidate_count": candidate_count,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "duplicate_provider_fixture_ids": duplicate_provider_fixture_ids,
        "missing_required_fields": missing_required_fields,
        "ready_for_future_staging_ingestion": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _has_payload_top_level_keys(payload_top_level_keys: Sequence[str]) -> bool:
    try:
        return any(
            bool(key.strip())
            for key in payload_top_level_keys
            if isinstance(key, str)
        )
    except TypeError:
        return False


def _duplicate_provider_fixture_ids(
    normalized_fixtures: Sequence[Mapping[str, Any]],
) -> list[int]:
    fixture_ids = [
        fixture_id
        for fixture in normalized_fixtures
        if (fixture_id := _positive_int_like(fixture.get("provider_fixture_id")))
        is not None
    ]
    counts = Counter(fixture_ids)
    return sorted(fixture_id for fixture_id, count in counts.items() if count > 1)


def _missing_required_fields(fixture: Mapping[str, Any]) -> list[str]:
    return [
        field_name
        for field_name in REQUIRED_FIXTURE_STAGING_FIELDS
        if not _has_required_value(field_name, fixture.get(field_name))
    ]


def _has_required_value(field_name: str, value: Any) -> bool:
    if field_name in NUMERIC_FIXTURE_STAGING_FIELDS:
        return _positive_int_like(value) is not None
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


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


def _present_forbidden_fixture_fields(fixture: Mapping[str, Any]) -> list[str]:
    return sorted(
        field_name
        for field_name in FORBIDDEN_FIXTURE_STAGING_FIELDS
        if field_name in fixture
    )


def _candidate_reference(index: int, fixture: Mapping[str, Any]) -> str:
    fixture_id = _positive_int_like(fixture.get("provider_fixture_id"))
    if fixture_id is not None:
        return f"provider_fixture_id:{fixture_id}"
    return f"candidate:{index}"


def _blocking_reasons(
    *,
    candidate_count: int,
    source_mode_present: bool,
    payload_hash_present: bool,
    payload_top_level_keys_present: bool,
    wrong_provider_found: bool,
    missing_required_fields_found: bool,
    duplicate_provider_fixture_ids_found: bool,
    forbidden_fixture_fields_found: bool,
) -> list[str]:
    reasons: list[str] = []
    if candidate_count == 0:
        reasons.append("no_candidates")
    if not source_mode_present:
        reasons.append("source_mode_missing")
    if not payload_hash_present:
        reasons.append("payload_hash_missing")
    if not payload_top_level_keys_present:
        reasons.append("payload_top_level_keys_missing")
    if wrong_provider_found:
        reasons.append("wrong_provider")
    if missing_required_fields_found:
        reasons.append("missing_required_fields")
    if duplicate_provider_fixture_ids_found:
        reasons.append("duplicate_provider_fixture_ids")
    if forbidden_fixture_fields_found:
        reasons.append("forbidden_fixture_fields")
    return reasons


__all__ = [
    "API_FOOTBALL_PROVIDER",
    "FIXTURE_STAGING_GATE_MODE",
    "FIXTURE_STAGING_TARGET_TABLE",
    "build_fixture_staging_ingestion_gate",
]
