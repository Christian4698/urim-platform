from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date as calendar_date
import re
from types import MappingProxyType
from typing import Final


API_FOOTBALL_FIXTURE_REQUEST_PROVIDER: Final = "api-football"
API_FOOTBALL_FIXTURE_REQUEST_ENDPOINT: Final = "/fixtures"
API_FOOTBALL_FIXTURE_REQUEST_METHOD: Final = "GET"

API_FOOTBALL_FIXTURE_ALLOWED_QUERY_KEYS: Final = (
    "league",
    "season",
    "team",
    "date",
    "from",
    "to",
    "timezone",
    "status",
)
API_FOOTBALL_FIXTURE_FORBIDDEN_QUERY_KEYS: Final = (
    "odds",
    "bookmaker",
    "stake",
    "prediction",
    "predictions",
    "bet",
    "betting",
)

_DATE_PATTERN: Final = re.compile(r"\d{4}-\d{2}-\d{2}")

FixtureQueryValue = int | str


class ApiFootballFixtureRequestValidationError(ValueError):
    """Raised when a Phase 27 fixture query is outside the safe allowlist."""


@dataclass(frozen=True)
class ApiFootballFixtureReadOnlyRequest:
    query: Mapping[str, FixtureQueryValue] = field(
        default_factory=lambda: MappingProxyType({})
    )
    provider: str = API_FOOTBALL_FIXTURE_REQUEST_PROVIDER
    endpoint: str = API_FOOTBALL_FIXTURE_REQUEST_ENDPOINT
    method: str = API_FOOTBALL_FIXTURE_REQUEST_METHOD
    read_only: bool = True
    db_writes: bool = False
    prediction_requested: bool = False
    betting_requested: bool = False

    def public_safe_summary(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "endpoint": self.endpoint,
            "method": self.method,
            "read_only": self.read_only,
            "query": dict(self.query),
            "db_writes": self.db_writes,
            "prediction_requested": self.prediction_requested,
            "betting_requested": self.betting_requested,
        }


def build_api_football_fixture_read_only_request(
    query: Mapping[str, object] | None = None,
) -> ApiFootballFixtureReadOnlyRequest:
    validated_query = _validate_fixture_query(query)
    return ApiFootballFixtureReadOnlyRequest(
        query=MappingProxyType(dict(validated_query))
    )


def _validate_fixture_query(
    query: Mapping[str, object] | None,
) -> dict[str, FixtureQueryValue]:
    if query is None:
        return {}
    if not isinstance(query, Mapping):
        raise ApiFootballFixtureRequestValidationError(
            "Fixture query must be a mapping."
        )

    _reject_unknown_or_forbidden_keys(query)

    validated: dict[str, FixtureQueryValue] = {}
    parsed_dates: dict[str, calendar_date] = {}
    for key in API_FOOTBALL_FIXTURE_ALLOWED_QUERY_KEYS:
        if key not in query:
            continue
        value = query[key]
        if key in {"league", "team"}:
            validated[key] = _validate_positive_int(key, value)
        elif key == "season":
            validated[key] = _validate_season(value)
        elif key in {"date", "from", "to"}:
            validated_date, parsed_date = _validate_date(key, value)
            validated[key] = validated_date
            parsed_dates[key] = parsed_date
        elif key in {"timezone", "status"}:
            validated[key] = _validate_non_empty_string(key, value)

    if "from" in parsed_dates and "to" in parsed_dates:
        if parsed_dates["from"] > parsed_dates["to"]:
            raise ApiFootballFixtureRequestValidationError(
                "Fixture query 'from' must be earlier than or equal to 'to'."
            )

    return validated


def _reject_unknown_or_forbidden_keys(query: Mapping[str, object]) -> None:
    for key in query:
        if not isinstance(key, str):
            raise ApiFootballFixtureRequestValidationError(
                "Fixture query keys must be strings."
            )

        normalized_key = key.strip().lower()
        if normalized_key in API_FOOTBALL_FIXTURE_FORBIDDEN_QUERY_KEYS:
            raise ApiFootballFixtureRequestValidationError(
                f"Fixture query parameter '{key}' is forbidden in Phase 27."
            )
        if key not in API_FOOTBALL_FIXTURE_ALLOWED_QUERY_KEYS:
            raise ApiFootballFixtureRequestValidationError(
                f"Unknown fixture query parameter '{key}'."
            )


def _validate_positive_int(key: str, value: object) -> int:
    if not _is_plain_int(value) or value <= 0:
        raise ApiFootballFixtureRequestValidationError(
            f"Fixture query '{key}' must be a positive integer."
        )
    return value


def _validate_season(value: object) -> int:
    if not _is_plain_int(value):
        raise ApiFootballFixtureRequestValidationError(
            "Fixture query 'season' must be a four digit integer."
        )
    if value < 1900 or value > 2100:
        raise ApiFootballFixtureRequestValidationError(
            "Fixture query 'season' must be between 1900 and 2100."
        )
    return value


def _validate_date(
    key: str,
    value: object,
) -> tuple[str, calendar_date]:
    if not isinstance(value, str) or not _DATE_PATTERN.fullmatch(value):
        raise ApiFootballFixtureRequestValidationError(
            f"Fixture query '{key}' must use YYYY-MM-DD format."
        )
    try:
        parsed_date = calendar_date.fromisoformat(value)
    except ValueError as exc:
        raise ApiFootballFixtureRequestValidationError(
            f"Fixture query '{key}' must be a valid calendar date."
        ) from exc
    return value, parsed_date


def _validate_non_empty_string(key: str, value: object) -> str:
    if not isinstance(value, str):
        raise ApiFootballFixtureRequestValidationError(
            f"Fixture query '{key}' must be a non-empty string."
        )
    trimmed_value = value.strip()
    if not trimmed_value:
        raise ApiFootballFixtureRequestValidationError(
            f"Fixture query '{key}' must be a non-empty string."
        )
    return trimmed_value


def _is_plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
