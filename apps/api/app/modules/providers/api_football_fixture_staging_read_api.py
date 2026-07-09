from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
import re
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
FIXTURE_STAGING_READ_API_MODE: Final = "fixture_staging_internal_read_only_api"
FIXTURE_STAGING_TARGET_TABLE: Final = "api_football_fixture_staging"
DEFAULT_FIXTURE_STAGING_READ_LIMIT: Final = 50
MAX_FIXTURE_STAGING_READ_LIMIT: Final = 100

ALLOWED_FIXTURE_STAGING_OUTPUT_FIELDS: Final = (
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
    "goals_home",
    "goals_away",
    "score_halftime_home",
    "score_halftime_away",
    "score_fulltime_home",
    "score_fulltime_away",
    "payload_hash",
    "payload_top_level_keys",
    "fetched_at",
    "source_mode",
)

_DATE_PATTERN: Final = re.compile(r"\d{4}-\d{2}-\d{2}")


class ApiFootballFixtureStagingReadApiValidationError(ValueError):
    """Raised when a Phase 40 internal read request is outside the safe contract."""


def build_fixture_staging_read_query(
    *,
    provider: str = API_FOOTBALL_PROVIDER,
    provider_league_id: int | None = None,
    provider_season: int | None = None,
    fixture_status_short: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = DEFAULT_FIXTURE_STAGING_READ_LIMIT,
    offset: int = 0,
) -> dict[str, Any]:
    if provider != API_FOOTBALL_PROVIDER:
        raise ApiFootballFixtureStagingReadApiValidationError(
            "Fixture staging reads are limited to api-football."
        )

    filters: dict[str, int | str] = {}
    if provider_league_id is not None:
        filters["provider_league_id"] = _validate_positive_int(
            "provider_league_id",
            provider_league_id,
        )
    if provider_season is not None:
        filters["provider_season"] = _validate_season(provider_season)
    if fixture_status_short is not None:
        filters["fixture_status_short"] = _validate_non_empty_string(
            "fixture_status_short",
            fixture_status_short,
        )

    parsed_date_from: date | None = None
    parsed_date_to: date | None = None
    if date_from is not None:
        filters["date_from"] = _validate_date("date_from", date_from)
        parsed_date_from = date.fromisoformat(filters["date_from"])
    if date_to is not None:
        filters["date_to"] = _validate_date("date_to", date_to)
        parsed_date_to = date.fromisoformat(filters["date_to"])
    if (
        parsed_date_from is not None
        and parsed_date_to is not None
        and parsed_date_from > parsed_date_to
    ):
        raise ApiFootballFixtureStagingReadApiValidationError(
            "date_from must be earlier than or equal to date_to."
        )

    validated_limit = _validate_limit(limit)
    validated_offset = _validate_offset(offset)

    return {
        "provider": API_FOOTBALL_PROVIDER,
        "mode": FIXTURE_STAGING_READ_API_MODE,
        "target_table": FIXTURE_STAGING_TARGET_TABLE,
        "read_only": True,
        "db_writes": False,
        "prediction_created": False,
        "betting_created": False,
        "filters": filters,
        "limit": validated_limit,
        "offset": validated_offset,
    }


def serialize_fixture_staging_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    query: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    read_query = _safe_query_summary(query)
    fixtures = [_serialize_fixture_row(row) for row in rows]

    return {
        "provider": read_query["provider"],
        "mode": read_query["mode"],
        "target_table": read_query["target_table"],
        "read_only": read_query["read_only"],
        "db_writes": read_query["db_writes"],
        "prediction_created": read_query["prediction_created"],
        "betting_created": read_query["betting_created"],
        "filters": read_query["filters"],
        "limit": read_query["limit"],
        "offset": read_query["offset"],
        "count": len(fixtures),
        "fixtures": fixtures,
    }


def _safe_query_summary(query: Mapping[str, Any] | None) -> dict[str, Any]:
    if query is None:
        return build_fixture_staging_read_query()
    if not isinstance(query, Mapping):
        raise ApiFootballFixtureStagingReadApiValidationError(
            "Fixture staging read query must be a mapping."
        )

    filters = query.get("filters", {})
    if not isinstance(filters, Mapping):
        raise ApiFootballFixtureStagingReadApiValidationError(
            "Fixture staging read query filters must be a mapping."
        )

    return build_fixture_staging_read_query(
        provider=query.get("provider", API_FOOTBALL_PROVIDER),
        provider_league_id=filters.get("provider_league_id"),
        provider_season=filters.get("provider_season"),
        fixture_status_short=filters.get("fixture_status_short"),
        date_from=filters.get("date_from"),
        date_to=filters.get("date_to"),
        limit=query.get("limit", DEFAULT_FIXTURE_STAGING_READ_LIMIT),
        offset=query.get("offset", 0),
    )


def _serialize_fixture_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        field_name: _public_value(field_name, row.get(field_name))
        for field_name in ALLOWED_FIXTURE_STAGING_OUTPUT_FIELDS
    }


def _public_value(field_name: str, value: Any) -> object:
    if field_name == "payload_top_level_keys":
        return _safe_payload_top_level_keys(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if value is None or isinstance(value, str | int | float | bool):
        return value
    return None


def _safe_payload_top_level_keys(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped_value = value.strip()
        return [stripped_value] if stripped_value else []
    if isinstance(value, Mapping):
        return sorted(str(key) for key in value)
    if isinstance(value, Sequence):
        return [str(item) for item in value if str(item).strip()]
    return []


def _validate_positive_int(key: str, value: Any) -> int:
    if not _is_plain_int(value) or value <= 0:
        raise ApiFootballFixtureStagingReadApiValidationError(
            f"{key} must be a positive integer."
        )
    return value


def _validate_season(value: Any) -> int:
    if not _is_plain_int(value):
        raise ApiFootballFixtureStagingReadApiValidationError(
            "provider_season must be a four digit integer."
        )
    if value < 1900 or value > 2100:
        raise ApiFootballFixtureStagingReadApiValidationError(
            "provider_season must be between 1900 and 2100."
        )
    return value


def _validate_non_empty_string(key: str, value: Any) -> str:
    if not isinstance(value, str):
        raise ApiFootballFixtureStagingReadApiValidationError(
            f"{key} must be a non-empty string."
        )
    trimmed_value = value.strip()
    if not trimmed_value:
        raise ApiFootballFixtureStagingReadApiValidationError(
            f"{key} must be a non-empty string."
        )
    return trimmed_value


def _validate_date(key: str, value: Any) -> str:
    if not isinstance(value, str) or not _DATE_PATTERN.fullmatch(value):
        raise ApiFootballFixtureStagingReadApiValidationError(
            f"{key} must use YYYY-MM-DD format."
        )
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ApiFootballFixtureStagingReadApiValidationError(
            f"{key} must be a valid calendar date."
        ) from exc
    return value


def _validate_limit(value: Any) -> int:
    if not _is_plain_int(value) or value < 1 or value > MAX_FIXTURE_STAGING_READ_LIMIT:
        raise ApiFootballFixtureStagingReadApiValidationError(
            "limit must be between 1 and 100."
        )
    return value


def _validate_offset(value: Any) -> int:
    if not _is_plain_int(value) or value < 0:
        raise ApiFootballFixtureStagingReadApiValidationError(
            "offset must be greater than or equal to zero."
        )
    return value


def _is_plain_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


__all__ = [
    "ALLOWED_FIXTURE_STAGING_OUTPUT_FIELDS",
    "API_FOOTBALL_PROVIDER",
    "ApiFootballFixtureStagingReadApiValidationError",
    "DEFAULT_FIXTURE_STAGING_READ_LIMIT",
    "FIXTURE_STAGING_READ_API_MODE",
    "FIXTURE_STAGING_TARGET_TABLE",
    "MAX_FIXTURE_STAGING_READ_LIMIT",
    "build_fixture_staging_read_query",
    "serialize_fixture_staging_rows",
]
