from __future__ import annotations

from datetime import datetime, timedelta, timezone
import inspect
import json
from pathlib import Path

import pytest

from app.modules.providers import (
    api_football_fixture_data_freshness_audit as audit_module,
)
from app.modules.providers.api_football_fixture_data_freshness_audit import (
    ApiFootballFixtureDataFreshnessAuditValidationError,
    build_fixture_data_freshness_audit,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "60_DATA_FRESHNESS_AND_PROVIDER_AUDIT_TRAIL.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "active"
    / "041-phase-41-data-freshness-provider-audit-trail.md"
)
COMPLETED_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "041-phase-41-data-freshness-provider-audit-trail.md"
)
NOW_UTC = datetime(2026, 7, 9, 12, 0, tzinfo=timezone.utc)
EXPECTED_OUTPUT_KEYS = {
    "provider",
    "mode",
    "target_table",
    "read_only",
    "db_writes",
    "prediction_created",
    "betting_created",
    "freshness_threshold_minutes",
    "row_count",
    "fresh_count",
    "stale_count",
    "missing_fetched_at_count",
    "invalid_fetched_at_count",
    "payload_hash_present_count",
    "payload_hash_missing_count",
    "payload_top_level_keys_present_count",
    "source_modes",
    "fixture_status_short_counts",
    "provider_fixture_id_missing_count",
    "ready_for_internal_read",
    "blocking_reasons",
}
FORBIDDEN_ROW_FIELDS = {
    "raw_payload",
    "api_key",
    "secret",
    "auth",
    "token",
    "odds",
    "bookmaker",
    "stake",
    "prediction",
    "predictions",
    "betting",
}


def _literal(*parts: str) -> str:
    return "".join(parts)


def _row(
    *,
    provider: object = "api-football",
    provider_fixture_id: object = 101,
    fetched_at: object | None = None,
    source_mode: object = "phase_40_read_only_test",
    payload_hash: object = "abc123",
    payload_top_level_keys: object = ("response", "results"),
    fixture_status_short: object = "NS",
) -> dict[str, object]:
    return {
        "provider": provider,
        "provider_fixture_id": provider_fixture_id,
        "fetched_at": NOW_UTC - timedelta(minutes=30)
        if fetched_at is None
        else fetched_at,
        "source_mode": source_mode,
        "payload_hash": payload_hash,
        "payload_top_level_keys": payload_top_level_keys,
        "fixture_status_short": fixture_status_short,
        "raw_payload": {"blocked": True},
        "api_key": "blocked-api-key",
        "secret": "blocked-secret",
        "auth": "blocked-auth",
        "token": "blocked-token",
        "odds": {"home": 1.5},
        "bookmaker": "blocked-bookmaker",
        "stake": 100,
        "prediction": "blocked-prediction",
        "predictions": ["blocked-predictions"],
        "betting": "blocked-betting",
    }


def test_fixture_data_freshness_audit_module_and_function_exist() -> None:
    assert hasattr(audit_module, "build_fixture_data_freshness_audit")
    assert callable(build_fixture_data_freshness_audit)


def test_fixture_data_freshness_audit_accepts_complete_fresh_row() -> None:
    result = build_fixture_data_freshness_audit([_row()], now_utc=NOW_UTC)

    assert set(result) == EXPECTED_OUTPUT_KEYS
    assert result["provider"] == "api-football"
    assert result["mode"] == "fixture_data_freshness_provider_audit_trail"
    assert result["target_table"] == "api_football_fixture_staging"
    assert result["read_only"] is True
    assert result["db_writes"] is False
    assert result["prediction_created"] is False
    assert result["betting_created"] is False
    assert result["freshness_threshold_minutes"] == 180
    assert result["row_count"] == 1
    assert result["fresh_count"] == 1
    assert result["stale_count"] == 0
    assert result["missing_fetched_at_count"] == 0
    assert result["invalid_fetched_at_count"] == 0
    assert result["payload_hash_present_count"] == 1
    assert result["payload_hash_missing_count"] == 0
    assert result["payload_top_level_keys_present_count"] == 1
    assert result["source_modes"] == ["phase_40_read_only_test"]
    assert result["fixture_status_short_counts"] == {"NS": 1}
    assert result["provider_fixture_id_missing_count"] == 0
    assert result["ready_for_internal_read"] is True
    assert result["blocking_reasons"] == []


def test_fixture_data_freshness_audit_aggregates_counts() -> None:
    row_with_missing_fetched_at = _row(provider_fixture_id=103, payload_hash="")
    row_with_missing_fetched_at.pop("fetched_at")
    rows = [
        _row(provider_fixture_id=101, fetched_at=NOW_UTC - timedelta(minutes=10)),
        _row(
            provider_fixture_id=102,
            fetched_at=(NOW_UTC - timedelta(minutes=200)).isoformat(),
            source_mode="phase_41_fixture_audit_test",
            fixture_status_short="FT",
        ),
        row_with_missing_fetched_at,
        _row(provider_fixture_id=None, fetched_at="not-a-date", fixture_status_short=""),
    ]

    result = build_fixture_data_freshness_audit(rows, now_utc=NOW_UTC)

    assert result["row_count"] == 4
    assert result["fresh_count"] == 1
    assert result["stale_count"] == 1
    assert result["missing_fetched_at_count"] == 1
    assert result["invalid_fetched_at_count"] == 1
    assert result["payload_hash_present_count"] == 3
    assert result["payload_hash_missing_count"] == 1
    assert result["payload_top_level_keys_present_count"] == 4
    assert result["source_modes"] == [
        "phase_40_read_only_test",
        "phase_41_fixture_audit_test",
    ]
    assert result["fixture_status_short_counts"] == {"FT": 1, "NS": 2}
    assert result["provider_fixture_id_missing_count"] == 1
    assert result["ready_for_internal_read"] is False
    assert result["blocking_reasons"] == [
        "stale_rows",
        "missing_fetched_at",
        "invalid_fetched_at",
        "payload_hash_missing",
        "provider_fixture_id_missing",
    ]


def test_fixture_data_freshness_audit_counts_iso_z_timestamp_as_fresh() -> None:
    result = build_fixture_data_freshness_audit(
        [_row(fetched_at="2026-07-09T10:00:00Z")],
        now_utc=NOW_UTC,
        freshness_threshold_minutes=180,
    )

    assert result["fresh_count"] == 1
    assert result["stale_count"] == 0
    assert result["ready_for_internal_read"] is True


def test_fixture_data_freshness_audit_marks_stale_rows_as_blocking() -> None:
    result = build_fixture_data_freshness_audit(
        [_row(fetched_at=NOW_UTC - timedelta(minutes=181))],
        now_utc=NOW_UTC,
    )

    assert result["fresh_count"] == 0
    assert result["stale_count"] == 1
    assert result["ready_for_internal_read"] is False
    assert "stale_rows" in result["blocking_reasons"]


def test_fixture_data_freshness_audit_blocks_empty_rows() -> None:
    result = build_fixture_data_freshness_audit([], now_utc=NOW_UTC)

    assert result["row_count"] == 0
    assert result["ready_for_internal_read"] is False
    assert result["blocking_reasons"] == ["no_rows"]


def test_fixture_data_freshness_audit_blocks_wrong_provider() -> None:
    result = build_fixture_data_freshness_audit(
        [_row(provider="other-provider")],
        now_utc=NOW_UTC,
    )

    assert result["ready_for_internal_read"] is False
    assert "wrong_provider" in result["blocking_reasons"]


def test_fixture_data_freshness_audit_blocks_missing_payload_top_level_keys() -> None:
    result = build_fixture_data_freshness_audit(
        [_row(payload_top_level_keys=[])],
        now_utc=NOW_UTC,
    )

    assert result["payload_top_level_keys_present_count"] == 0
    assert result["ready_for_internal_read"] is False
    assert "payload_top_level_keys_missing" in result["blocking_reasons"]


def test_fixture_data_freshness_audit_marks_future_fetched_at_invalid() -> None:
    result = build_fixture_data_freshness_audit(
        [_row(fetched_at=NOW_UTC + timedelta(minutes=1))],
        now_utc=NOW_UTC,
    )

    assert result["invalid_fetched_at_count"] == 1
    assert result["ready_for_internal_read"] is False
    assert "invalid_fetched_at" in result["blocking_reasons"]


@pytest.mark.parametrize("threshold", [0, -1, True])
def test_fixture_data_freshness_audit_rejects_non_positive_threshold(
    threshold: object,
) -> None:
    with pytest.raises(ApiFootballFixtureDataFreshnessAuditValidationError):
        build_fixture_data_freshness_audit(
            [_row()],
            now_utc=NOW_UTC,
            freshness_threshold_minutes=threshold,  # type: ignore[arg-type]
        )


def test_fixture_data_freshness_audit_requires_now_utc_argument() -> None:
    with pytest.raises(TypeError):
        build_fixture_data_freshness_audit([_row()])  # type: ignore[call-arg]


@pytest.mark.parametrize(
    "now_value",
    [
        datetime(2026, 7, 9, 12, 0),
        datetime(2026, 7, 9, 12, 0, tzinfo=timezone(timedelta(hours=1))),
        "2026-07-09T12:00:00+00:00",
    ],
)
def test_fixture_data_freshness_audit_rejects_invalid_now_utc(
    now_value: object,
) -> None:
    with pytest.raises(ApiFootballFixtureDataFreshnessAuditValidationError):
        build_fixture_data_freshness_audit(
            [_row()],
            now_utc=now_value,  # type: ignore[arg-type]
        )


def test_fixture_data_freshness_audit_output_does_not_echo_forbidden_row_material() -> None:
    result = build_fixture_data_freshness_audit([_row()], now_utc=NOW_UTC)
    serialized_result = json.dumps(result, sort_keys=True)

    assert "blocked" not in serialized_result
    assert "raw_payload" not in serialized_result
    assert "api_key" not in serialized_result
    assert "auth" not in serialized_result
    assert "secret" not in serialized_result
    assert "token" not in serialized_result
    assert "odds" not in serialized_result
    assert "bookmaker" not in serialized_result
    assert "stake" not in serialized_result
    assert "predictions" not in serialized_result


def test_fixture_data_freshness_audit_source_has_no_writes_provider_calls_or_secret_material() -> None:
    module_source = inspect.getsource(audit_module).lower()

    forbidden_fragments = (
        _literal("in", "sert"),
        _literal("up", "date"),
        _literal("del", "ete"),
        "upsert",
        "session.add",
        ".execute(",
        "sqlalchemy",
        "commit",
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "urlopen",
        "socket",
        _literal("api", "_key"),
        _literal("x", "-apisports-key"),
        _literal("api-football", ".com"),
        _literal("api", "-sports"),
        _literal("rapid", "api"),
        _literal("au", "th"),
        _literal("bear", "er"),
        _literal("tok", "en"),
        _literal("sec", "ret"),
        _literal("raw", "_payload"),
    )
    for fragment in forbidden_fragments:
        assert fragment not in module_source


def test_fixture_data_freshness_audit_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 41" in doc_text
    assert "read-only audit only" in doc_lower
    assert "no real api call" in doc_lower
    assert "no db write" in doc_lower
    assert "no ingestion runtime" in doc_lower
    assert "no prediction/scoring" in doc_lower
    assert "no betting/odds" in doc_lower
    assert "phase 42" in doc_lower
    assert "feature snapshot contract" in doc_lower
    assert "without ml" in doc_lower


def test_fixture_data_freshness_audit_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "60_DATA_FRESHNESS_AND_PROVIDER_AUDIT_TRAIL.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
