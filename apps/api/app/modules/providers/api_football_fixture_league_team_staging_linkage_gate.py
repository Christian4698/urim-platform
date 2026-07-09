from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
FIXTURE_LINKAGE_GATE_MODE: Final = "fixture_league_team_staging_linkage_gate_only"
FIXTURE_LINKAGE_TARGET_TABLE: Final = "api_football_fixture_staging"

FORBIDDEN_LINKAGE_FIELDS: Final = frozenset(
    {"odds", "bookmaker", "stake", "prediction", "betting"}
)


def build_fixture_league_team_staging_linkage_gate(
    fixtures: Sequence[Mapping[str, Any]],
    leagues: Sequence[Mapping[str, Any]],
    teams: Sequence[Mapping[str, Any]],
    *,
    source_mode: str,
    payload_hashes: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    source_mode_value = _safe_text(source_mode)
    fixture_count = len(fixtures)
    league_count = len(leagues)
    team_count = len(teams)

    league_ids = _positive_id_set(leagues, "provider_league_id")
    team_ids = _positive_id_set(teams, "provider_team_id")
    duplicate_league_ids = _duplicate_positive_ids(leagues, "provider_league_id")
    duplicate_team_ids = _duplicate_positive_ids(teams, "provider_team_id")
    duplicate_league_id_set = set(duplicate_league_ids)
    duplicate_team_id_set = set(duplicate_team_ids)

    linked_fixture_count = 0
    missing_league_reference_count = 0
    missing_home_team_reference_count = 0
    missing_away_team_reference_count = 0
    wrong_provider_found = False
    forbidden_fields_found = (
        _has_forbidden_fields(fixtures)
        or _has_forbidden_fields(leagues)
        or _has_forbidden_fields(teams)
    )

    for fixture in fixtures:
        provider_ok = fixture.get("provider") == API_FOOTBALL_PROVIDER
        if not provider_ok:
            wrong_provider_found = True

        league_id = _positive_int_like(fixture.get("provider_league_id"))
        home_team_id = _positive_int_like(fixture.get("home_team_provider_id"))
        away_team_id = _positive_int_like(fixture.get("away_team_provider_id"))

        missing_league_reference = league_id is None or league_id not in league_ids
        missing_home_team_reference = (
            home_team_id is None or home_team_id not in team_ids
        )
        missing_away_team_reference = (
            away_team_id is None or away_team_id not in team_ids
        )

        if missing_league_reference:
            missing_league_reference_count += 1
        if missing_home_team_reference:
            missing_home_team_reference_count += 1
        if missing_away_team_reference:
            missing_away_team_reference_count += 1

        ambiguous_reference = (
            league_id in duplicate_league_id_set
            or home_team_id in duplicate_team_id_set
            or away_team_id in duplicate_team_id_set
        )
        fixture_has_forbidden_fields = bool(_present_forbidden_fields(fixture))

        if (
            provider_ok
            and not missing_league_reference
            and not missing_home_team_reference
            and not missing_away_team_reference
            and not ambiguous_reference
            and not fixture_has_forbidden_fields
        ):
            linked_fixture_count += 1

    blocking_reasons = _blocking_reasons(
        fixture_count=fixture_count,
        source_mode_present=bool(source_mode_value),
        wrong_provider_found=wrong_provider_found,
        missing_league_reference_found=missing_league_reference_count > 0,
        missing_home_team_reference_found=missing_home_team_reference_count > 0,
        missing_away_team_reference_found=missing_away_team_reference_count > 0,
        duplicate_league_ids_found=bool(duplicate_league_ids),
        duplicate_team_ids_found=bool(duplicate_team_ids),
        forbidden_fields_found=forbidden_fields_found,
    )

    return {
        "provider": API_FOOTBALL_PROVIDER,
        "mode": FIXTURE_LINKAGE_GATE_MODE,
        "target_table": FIXTURE_LINKAGE_TARGET_TABLE,
        "db_writes": False,
        "prediction_created": False,
        "betting_created": False,
        "source_mode": source_mode_value,
        "fixture_count": fixture_count,
        "league_count": league_count,
        "team_count": team_count,
        "linked_fixture_count": linked_fixture_count,
        "unlinked_fixture_count": fixture_count - linked_fixture_count,
        "missing_league_reference_count": missing_league_reference_count,
        "missing_home_team_reference_count": missing_home_team_reference_count,
        "missing_away_team_reference_count": missing_away_team_reference_count,
        "duplicate_league_ids": duplicate_league_ids,
        "duplicate_team_ids": duplicate_team_ids,
        "ready_for_future_staging_linkage": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _positive_id_set(
    records: Sequence[Mapping[str, Any]],
    field_name: str,
) -> set[int]:
    return {
        parsed_value
        for record in records
        if (parsed_value := _positive_int_like(record.get(field_name))) is not None
    }


def _duplicate_positive_ids(
    records: Sequence[Mapping[str, Any]],
    field_name: str,
) -> list[int]:
    ids = [
        parsed_value
        for record in records
        if (parsed_value := _positive_int_like(record.get(field_name))) is not None
    ]
    counts = Counter(ids)
    return sorted(parsed_value for parsed_value, count in counts.items() if count > 1)


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


def _has_forbidden_fields(records: Sequence[Mapping[str, Any]]) -> bool:
    return any(_present_forbidden_fields(record) for record in records)


def _present_forbidden_fields(record: Mapping[str, Any]) -> list[str]:
    return sorted(
        field_name
        for field_name in FORBIDDEN_LINKAGE_FIELDS
        if any(str(key).strip().lower() == field_name for key in record)
    )


def _blocking_reasons(
    *,
    fixture_count: int,
    source_mode_present: bool,
    wrong_provider_found: bool,
    missing_league_reference_found: bool,
    missing_home_team_reference_found: bool,
    missing_away_team_reference_found: bool,
    duplicate_league_ids_found: bool,
    duplicate_team_ids_found: bool,
    forbidden_fields_found: bool,
) -> list[str]:
    reasons: list[str] = []
    if fixture_count == 0:
        reasons.append("no_fixtures")
    if not source_mode_present:
        reasons.append("source_mode_missing")
    if wrong_provider_found:
        reasons.append("wrong_provider")
    if missing_league_reference_found:
        reasons.append("missing_league_reference")
    if missing_home_team_reference_found:
        reasons.append("missing_home_team_reference")
    if missing_away_team_reference_found:
        reasons.append("missing_away_team_reference")
    if duplicate_league_ids_found:
        reasons.append("duplicate_league_ids")
    if duplicate_team_ids_found:
        reasons.append("duplicate_team_ids")
    if forbidden_fields_found:
        reasons.append("forbidden_fields")
    return reasons


__all__ = [
    "API_FOOTBALL_PROVIDER",
    "FIXTURE_LINKAGE_GATE_MODE",
    "FIXTURE_LINKAGE_TARGET_TABLE",
    "build_fixture_league_team_staging_linkage_gate",
]
