from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
FIXTURE_BASELINE_ANALYTICS_MODE: Final = (
    "fixture_baseline_analytics_without_official_prediction"
)
DEFAULT_ANALYTICS_SCHEMA_VERSION: Final = "fixture_baseline_analytics_v1"
DEFAULT_ANALYTICS_SOURCE_MODE: Final = "feature_snapshot_contract"

ALLOWED_BASELINE_ANALYTICS_INPUT_KEYS: Final = (
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

_COMPLETED_STATUS_SHORT_VALUES: Final = frozenset({"FT", "AET", "PEN"})
_LIVE_STATUS_SHORT_VALUES: Final = frozenset(
    {"1H", "HT", "2H", "ET", "BT", "P", "SUSP", "INT", "LIVE"}
)
_SCHEDULED_STATUS_SHORT_VALUES: Final = frozenset({"NS", "TBD"})
_CANCELLED_OR_POSTPONED_STATUS_SHORT_VALUES: Final = frozenset(
    {"PST", "CANC", "ABD"}
)


def build_fixture_baseline_analytics(
    snapshot_candidates: Sequence[Mapping[str, Any]],
    *,
    analytics_schema_version: str = DEFAULT_ANALYTICS_SCHEMA_VERSION,
    source_mode: str = DEFAULT_ANALYTICS_SOURCE_MODE,
) -> dict[str, Any]:
    analytics_schema_version_value = _safe_text(analytics_schema_version)
    source_mode_value = _safe_text(source_mode)
    global_blocking_reasons = _global_blocking_reasons(
        analytics_schema_version_present=bool(analytics_schema_version_value),
        source_mode_present=bool(source_mode_value),
    )

    accepted_candidates: list[Mapping[str, Any]] = []
    row_rejection_reasons: set[str] = set()

    for candidate in snapshot_candidates:
        missing_reasons = _candidate_rejection_reasons(candidate)
        for reason in missing_reasons:
            row_rejection_reasons.add(reason)
        if missing_reasons or global_blocking_reasons:
            continue
        accepted_candidates.append(candidate)

    status_counts = _status_counts(accepted_candidates)
    league_counts = _field_counts(accepted_candidates, "provider_league_id")
    season_counts = _field_counts(accepted_candidates, "provider_season")
    completed_fixture_count = _status_family_count(
        status_counts,
        _COMPLETED_STATUS_SHORT_VALUES,
    )
    live_fixture_count = _status_family_count(
        status_counts,
        _LIVE_STATUS_SHORT_VALUES,
    )
    scheduled_fixture_count = _status_family_count(
        status_counts,
        _SCHEDULED_STATUS_SHORT_VALUES,
    )
    cancelled_or_postponed_count = _status_family_count(
        status_counts,
        _CANCELLED_OR_POSTPONED_STATUS_SHORT_VALUES,
    )
    blocking_reasons = [
        *global_blocking_reasons,
        *sorted(row_rejection_reasons),
    ]

    return {
        "provider": API_FOOTBALL_PROVIDER,
        "mode": FIXTURE_BASELINE_ANALYTICS_MODE,
        "read_only": True,
        "db_writes": False,
        "prediction_created": False,
        "official_prediction_created": False,
        "betting_created": False,
        "ml_model_used": False,
        "confidence_score_created": False,
        "analytics_schema_version": analytics_schema_version_value,
        "source_mode": source_mode_value,
        "candidate_count": len(snapshot_candidates),
        "accepted_count": len(accepted_candidates),
        "rejected_count": len(snapshot_candidates) - len(accepted_candidates),
        "fixture_status_short_counts": dict(sorted(status_counts.items())),
        "league_counts": dict(sorted(league_counts.items())),
        "season_counts": dict(sorted(season_counts.items())),
        "completed_fixture_count": completed_fixture_count,
        "live_fixture_count": live_fixture_count,
        "scheduled_fixture_count": scheduled_fixture_count,
        "cancelled_or_postponed_count": cancelled_or_postponed_count,
        "goals_summary": _goals_summary(accepted_candidates),
        "descriptive_signals": {
            "has_completed_sample": completed_fixture_count > 0,
            "has_live_sample": live_fixture_count > 0,
            "has_scheduled_sample": scheduled_fixture_count > 0,
            "sample_is_empty": len(accepted_candidates) == 0,
        },
        "blocking_reasons": blocking_reasons,
    }


def _global_blocking_reasons(
    *,
    analytics_schema_version_present: bool,
    source_mode_present: bool,
) -> list[str]:
    reasons: list[str] = []
    if not analytics_schema_version_present:
        reasons.append("analytics_schema_version_missing")
    if not source_mode_present:
        reasons.append("source_mode_missing")
    return reasons


def _candidate_rejection_reasons(candidate: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if candidate.get("provider") != API_FOOTBALL_PROVIDER:
        reasons.append("wrong_provider")
    if _positive_int_like(candidate.get("provider_fixture_id")) is None:
        reasons.append("provider_fixture_id_missing")
    if _positive_int_like(candidate.get("provider_league_id")) is None:
        reasons.append("provider_league_id_missing")
    if not _safe_text(candidate.get("fixture_status_short")):
        reasons.append("fixture_status_short_missing")
    return reasons


def _status_counts(candidates: Sequence[Mapping[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for candidate in candidates:
        status_short = _normalized_status_short(candidate.get("fixture_status_short"))
        if status_short:
            counter[status_short] += 1
    return counter


def _field_counts(
    candidates: Sequence[Mapping[str, Any]],
    field_name: str,
) -> Counter[str]:
    counter: Counter[str] = Counter()
    for candidate in candidates:
        count_key = _count_key(candidate.get(field_name))
        if count_key is not None:
            counter[count_key] += 1
    return counter


def _status_family_count(
    status_counts: Mapping[str, int],
    status_family: frozenset[str],
) -> int:
    return sum(
        count
        for status_short, count in status_counts.items()
        if status_short in status_family
    )


def _goals_summary(candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    fixtures_with_fulltime_scores = 0
    home_goals_total = 0
    away_goals_total = 0

    for candidate in candidates:
        home_fulltime_score = _non_negative_int_like(
            candidate.get("score_fulltime_home")
        )
        away_fulltime_score = _non_negative_int_like(
            candidate.get("score_fulltime_away")
        )
        if home_fulltime_score is None or away_fulltime_score is None:
            continue
        fixtures_with_fulltime_scores += 1
        home_goals_total += home_fulltime_score
        away_goals_total += away_fulltime_score

    average_total_goals = None
    if fixtures_with_fulltime_scores:
        average_total_goals = (
            home_goals_total + away_goals_total
        ) / fixtures_with_fulltime_scores

    return {
        "fixtures_with_fulltime_scores": fixtures_with_fulltime_scores,
        "average_total_goals": average_total_goals,
        "home_goals_total": home_goals_total,
        "away_goals_total": away_goals_total,
    }


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _normalized_status_short(value: Any) -> str:
    return _safe_text(value).upper()


def _count_key(value: Any) -> str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        stripped_value = value.strip()
        return stripped_value or None
    return None


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


def _non_negative_int_like(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str):
        stripped_value = value.strip()
        if stripped_value.isdecimal():
            parsed_value = int(stripped_value)
            return parsed_value if parsed_value >= 0 else None
    return None


__all__ = [
    "ALLOWED_BASELINE_ANALYTICS_INPUT_KEYS",
    "API_FOOTBALL_PROVIDER",
    "DEFAULT_ANALYTICS_SCHEMA_VERSION",
    "DEFAULT_ANALYTICS_SOURCE_MODE",
    "FIXTURE_BASELINE_ANALYTICS_MODE",
    "build_fixture_baseline_analytics",
]
