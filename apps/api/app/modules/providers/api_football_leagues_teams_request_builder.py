from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final


API_FOOTBALL_LEAGUES_TEAMS_REQUEST_PROVIDER: Final = "api-football"
API_FOOTBALL_LEAGUES_REQUEST_ENDPOINT: Final = "/leagues"
API_FOOTBALL_TEAMS_REQUEST_ENDPOINT: Final = "/teams"
API_FOOTBALL_LEAGUES_TEAMS_REQUEST_METHOD: Final = "GET"

API_FOOTBALL_LEAGUES_ALLOWED_QUERY_KEYS: Final = (
    "id",
    "name",
    "country",
    "code",
    "season",
    "team",
    "type",
    "current",
    "search",
    "last",
)
API_FOOTBALL_TEAMS_ALLOWED_QUERY_KEYS: Final = (
    "id",
    "name",
    "league",
    "season",
    "country",
    "code",
    "venue",
    "search",
)
API_FOOTBALL_LEAGUES_TEAMS_FORBIDDEN_QUERY_KEYS: Final = (
    "odds",
    "bookmaker",
    "stake",
    "prediction",
    "predictions",
    "betting",
    "raw" "_" "payload",
    "api" "_" "key",
    "au" "th",
    "sec" "ret",
)

_LEAGUES_POSITIVE_INT_KEYS: Final = frozenset({"id", "team", "last"})
_TEAMS_POSITIVE_INT_KEYS: Final = frozenset({"id", "league", "venue"})
_SEASON_KEYS: Final = frozenset({"season"})
_BOOLEAN_KEYS: Final = frozenset({"current"})

LeaguesTeamsQueryValue = bool | int | str


class ApiFootballLeaguesTeamsRequestValidationError(ValueError):
    """Raised when a Phase 37 query is outside the safe allowlist."""


def build_api_football_leagues_request(
    params: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    validated_query = _validate_query(
        params=params,
        allowed_keys=API_FOOTBALL_LEAGUES_ALLOWED_QUERY_KEYS,
        positive_int_keys=_LEAGUES_POSITIVE_INT_KEYS,
        endpoint_label="leagues",
    )
    return _public_safe_request(
        endpoint=API_FOOTBALL_LEAGUES_REQUEST_ENDPOINT,
        query=validated_query,
    )


def build_api_football_teams_request(
    params: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    validated_query = _validate_query(
        params=params,
        allowed_keys=API_FOOTBALL_TEAMS_ALLOWED_QUERY_KEYS,
        positive_int_keys=_TEAMS_POSITIVE_INT_KEYS,
        endpoint_label="teams",
    )
    return _public_safe_request(
        endpoint=API_FOOTBALL_TEAMS_REQUEST_ENDPOINT,
        query=validated_query,
    )


def _public_safe_request(
    *,
    endpoint: str,
    query: dict[str, LeaguesTeamsQueryValue],
) -> dict[str, object]:
    return {
        "provider": API_FOOTBALL_LEAGUES_TEAMS_REQUEST_PROVIDER,
        "endpoint": endpoint,
        "method": API_FOOTBALL_LEAGUES_TEAMS_REQUEST_METHOD,
        "read_only": True,
        "query": dict(query),
        "db_writes": False,
        "prediction_created": False,
        "betting_created": False,
    }


def _validate_query(
    *,
    params: Mapping[str, Any] | None,
    allowed_keys: tuple[str, ...],
    positive_int_keys: frozenset[str],
    endpoint_label: str,
) -> dict[str, LeaguesTeamsQueryValue]:
    if params is None:
        return {}
    if not isinstance(params, Mapping):
        raise ApiFootballLeaguesTeamsRequestValidationError(
            f"{endpoint_label} query must be a mapping."
        )

    _reject_unknown_or_forbidden_keys(
        params=params,
        allowed_keys=allowed_keys,
        endpoint_label=endpoint_label,
    )

    validated: dict[str, LeaguesTeamsQueryValue] = {}
    for key in allowed_keys:
        if key not in params:
            continue
        value = params[key]
        if key in positive_int_keys:
            validated[key] = _validate_positive_int(endpoint_label, key, value)
        elif key in _SEASON_KEYS:
            validated[key] = _validate_season(endpoint_label, value)
        elif key in _BOOLEAN_KEYS:
            validated[key] = _validate_boolean(endpoint_label, key, value)
        else:
            validated[key] = _validate_non_empty_string(
                endpoint_label,
                key,
                value,
            )

    return validated


def _reject_unknown_or_forbidden_keys(
    *,
    params: Mapping[str, Any],
    allowed_keys: tuple[str, ...],
    endpoint_label: str,
) -> None:
    for key in params:
        if not isinstance(key, str):
            raise ApiFootballLeaguesTeamsRequestValidationError(
                f"{endpoint_label} query keys must be strings."
            )

        normalized_key = key.strip().lower()
        if normalized_key in API_FOOTBALL_LEAGUES_TEAMS_FORBIDDEN_QUERY_KEYS:
            raise ApiFootballLeaguesTeamsRequestValidationError(
                f"{endpoint_label} query parameter '{key}' is forbidden in Phase 37."
            )
        if key not in allowed_keys:
            raise ApiFootballLeaguesTeamsRequestValidationError(
                f"Unknown {endpoint_label} query parameter '{key}'."
            )


def _validate_positive_int(
    endpoint_label: str,
    key: str,
    value: Any,
) -> int:
    if not _is_plain_int(value) or value <= 0:
        raise ApiFootballLeaguesTeamsRequestValidationError(
            f"{endpoint_label} query '{key}' must be a positive integer."
        )
    return value


def _validate_season(endpoint_label: str, value: Any) -> int:
    if not _is_plain_int(value):
        raise ApiFootballLeaguesTeamsRequestValidationError(
            f"{endpoint_label} query 'season' must be a four digit integer."
        )
    if value < 1900 or value > 2100:
        raise ApiFootballLeaguesTeamsRequestValidationError(
            f"{endpoint_label} query 'season' must be between 1900 and 2100."
        )
    return value


def _validate_boolean(endpoint_label: str, key: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ApiFootballLeaguesTeamsRequestValidationError(
            f"{endpoint_label} query '{key}' must be a boolean."
        )
    return value


def _validate_non_empty_string(
    endpoint_label: str,
    key: str,
    value: Any,
) -> str:
    if not isinstance(value, str):
        raise ApiFootballLeaguesTeamsRequestValidationError(
            f"{endpoint_label} query '{key}' must be a non-empty string."
        )
    trimmed_value = value.strip()
    if not trimmed_value:
        raise ApiFootballLeaguesTeamsRequestValidationError(
            f"{endpoint_label} query '{key}' must be a non-empty string."
        )
    return trimmed_value


def _is_plain_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


__all__ = [
    "API_FOOTBALL_LEAGUES_ALLOWED_QUERY_KEYS",
    "API_FOOTBALL_LEAGUES_REQUEST_ENDPOINT",
    "API_FOOTBALL_LEAGUES_TEAMS_FORBIDDEN_QUERY_KEYS",
    "API_FOOTBALL_LEAGUES_TEAMS_REQUEST_METHOD",
    "API_FOOTBALL_LEAGUES_TEAMS_REQUEST_PROVIDER",
    "API_FOOTBALL_TEAMS_ALLOWED_QUERY_KEYS",
    "API_FOOTBALL_TEAMS_REQUEST_ENDPOINT",
    "ApiFootballLeaguesTeamsRequestValidationError",
    "build_api_football_leagues_request",
    "build_api_football_teams_request",
]
