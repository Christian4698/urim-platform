from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
FIXTURE_FEATURE_SNAPSHOT_CONTRACT_MODE: Final = (
    "fixture_feature_snapshot_contract_without_ml"
)
FEATURE_SNAPSHOT_TARGET_TABLE: Final = "feature_snapshots"
DEFAULT_FEATURE_SCHEMA_VERSION: Final = "fixture_features_v1"
DEFAULT_FEATURE_SOURCE_MODE: Final = "staging_read_only"

ALLOWED_FEATURE_KEYS: Final = (
    "provider",
    "provider_fixture_id",
    "provider_league_id",
    "provider_season",
    "fixture_date",
    "fixture_timezone",
    "fixture_status_short",
    "fixture_status_long",
    "home_team_provider_id",
    "away_team_provider_id",
    "goals_home",
    "goals_away",
    "score_halftime_home",
    "score_halftime_away",
    "score_fulltime_home",
    "score_fulltime_away",
    "payload_hash",
    "fetched_at",
    "source_mode",
    "feature_schema_version",
)


def build_fixture_feature_snapshot_contract(
    rows: Sequence[Mapping[str, Any]],
    *,
    feature_schema_version: str = DEFAULT_FEATURE_SCHEMA_VERSION,
    source_mode: str = DEFAULT_FEATURE_SOURCE_MODE,
) -> dict[str, Any]:
    feature_schema_version_value = _safe_text(feature_schema_version)
    source_mode_value = _safe_text(source_mode)
    global_blocking_reasons = _global_blocking_reasons(
        row_count=len(rows),
        feature_schema_version_present=bool(feature_schema_version_value),
        source_mode_present=bool(source_mode_value),
    )

    snapshot_candidates: list[dict[str, Any]] = []
    row_rejection_reasons: set[str] = set()

    for row in rows:
        missing_reasons = _row_rejection_reasons(row)
        for reason in missing_reasons:
            row_rejection_reasons.add(reason)
        if missing_reasons or global_blocking_reasons:
            continue
        snapshot_candidates.append(
            _snapshot_candidate(
                row,
                feature_schema_version=feature_schema_version_value,
                source_mode=source_mode_value,
            )
        )

    blocking_reasons = [
        *global_blocking_reasons,
        *sorted(row_rejection_reasons),
    ]

    return {
        "provider": API_FOOTBALL_PROVIDER,
        "mode": FIXTURE_FEATURE_SNAPSHOT_CONTRACT_MODE,
        "target_table": FEATURE_SNAPSHOT_TARGET_TABLE,
        "read_only": True,
        "db_writes": False,
        "prediction_created": False,
        "betting_created": False,
        "ml_model_used": False,
        "confidence_score_created": False,
        "feature_schema_version": feature_schema_version_value,
        "source_mode": source_mode_value,
        "candidate_count": len(rows),
        "accepted_count": len(snapshot_candidates),
        "rejected_count": len(rows) - len(snapshot_candidates),
        "allowed_feature_keys": list(ALLOWED_FEATURE_KEYS),
        "snapshot_candidates": snapshot_candidates,
        "blocking_reasons": blocking_reasons,
    }


def _global_blocking_reasons(
    *,
    row_count: int,
    feature_schema_version_present: bool,
    source_mode_present: bool,
) -> list[str]:
    reasons: list[str] = []
    if row_count == 0:
        reasons.append("no_rows")
    if not feature_schema_version_present:
        reasons.append("feature_schema_version_missing")
    if not source_mode_present:
        reasons.append("source_mode_missing")
    return reasons


def _row_rejection_reasons(row: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if row.get("provider") != API_FOOTBALL_PROVIDER:
        reasons.append("wrong_provider")
    if _positive_int_like(row.get("provider_fixture_id")) is None:
        reasons.append("provider_fixture_id_missing")
    if _positive_int_like(row.get("provider_league_id")) is None:
        reasons.append("provider_league_id_missing")
    if not _has_fixture_date(row.get("fixture_date")):
        reasons.append("fixture_date_missing")
    if not _has_text(row.get("payload_hash")):
        reasons.append("payload_hash_missing")
    return reasons


def _snapshot_candidate(
    row: Mapping[str, Any],
    *,
    feature_schema_version: str,
    source_mode: str,
) -> dict[str, Any]:
    candidate = {
        field_name: _public_value(row.get(field_name))
        for field_name in ALLOWED_FEATURE_KEYS
        if field_name not in {"feature_schema_version", "source_mode"}
    }
    candidate["source_mode"] = source_mode
    candidate["feature_schema_version"] = feature_schema_version
    return candidate


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_fixture_date(value: Any) -> bool:
    if isinstance(value, datetime | date):
        return True
    return isinstance(value, str) and bool(value.strip())


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


def _public_value(value: Any) -> object:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if value is None or isinstance(value, str | int | float | bool):
        return value
    return None


__all__ = [
    "ALLOWED_FEATURE_KEYS",
    "API_FOOTBALL_PROVIDER",
    "DEFAULT_FEATURE_SCHEMA_VERSION",
    "DEFAULT_FEATURE_SOURCE_MODE",
    "FEATURE_SNAPSHOT_TARGET_TABLE",
    "FIXTURE_FEATURE_SNAPSHOT_CONTRACT_MODE",
    "build_fixture_feature_snapshot_contract",
]
