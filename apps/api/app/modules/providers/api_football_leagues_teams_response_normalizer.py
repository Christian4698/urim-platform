from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import json
import math
from typing import Any, Final


API_FOOTBALL_LEAGUES_TEAMS_NORMALIZER_PROVIDER: Final = "api-football"
API_FOOTBALL_LEAGUES_NORMALIZER_ENDPOINT: Final = "/leagues"
API_FOOTBALL_TEAMS_NORMALIZER_ENDPOINT: Final = "/teams"
API_FOOTBALL_LEAGUES_NORMALIZER_MODE: Final = "leagues_response_normalizer_only"
API_FOOTBALL_TEAMS_NORMALIZER_MODE: Final = "teams_response_normalizer_only"

API_FOOTBALL_LEAGUE_NORMALIZED_FIELDS: Final = (
    ("provider_league_id", ("league", "id")),
    ("league_name", ("league", "name")),
    ("league_type", ("league", "type")),
    ("country_name", ("country", "name")),
    ("country_code", ("country", "code")),
)
API_FOOTBALL_LEAGUE_SEASON_NORMALIZED_FIELDS: Final = (
    ("season", ("year",)),
    ("season_start", ("start",)),
    ("season_end", ("end",)),
    ("season_current", ("current",)),
)
API_FOOTBALL_TEAM_NORMALIZED_FIELDS: Final = (
    ("provider_team_id", ("team", "id")),
    ("team_name", ("team", "name")),
    ("team_code", ("team", "code")),
    ("team_country", ("team", "country")),
    ("team_founded", ("team", "founded")),
    ("team_national", ("team", "national")),
    ("venue_provider_id", ("venue", "id")),
    ("venue_name", ("venue", "name")),
    ("venue_city", ("venue", "city")),
    ("venue_capacity", ("venue", "capacity")),
)

NormalizedLeaguesTeamsValue = str | int | float | bool | None


class ApiFootballLeaguesTeamsResponseNormalizationError(ValueError):
    """Raised when a Phase 38 payload is outside the safe local test contract."""


def normalize_api_football_leagues_response(
    payload: Mapping[str, Any],
) -> dict[str, object]:
    response = _response_items(payload, endpoint_label="leagues")
    leagues = [
        normalized_league
        for item in response
        for normalized_league in _normalize_league_item(item)
    ]

    return {
        "provider": API_FOOTBALL_LEAGUES_TEAMS_NORMALIZER_PROVIDER,
        "endpoint": API_FOOTBALL_LEAGUES_NORMALIZER_ENDPOINT,
        "mode": API_FOOTBALL_LEAGUES_NORMALIZER_MODE,
        "payload_hash": _stable_payload_hash(payload),
        "payload_top_level_keys": _top_level_keys(payload),
        "normalized_count": len(leagues),
        "leagues": leagues,
        "db_writes": False,
        "prediction_created": False,
        "betting_created": False,
    }


def normalize_api_football_teams_response(
    payload: Mapping[str, Any],
) -> dict[str, object]:
    response = _response_items(payload, endpoint_label="teams")
    teams = [_normalize_team_item(item) for item in response]

    return {
        "provider": API_FOOTBALL_LEAGUES_TEAMS_NORMALIZER_PROVIDER,
        "endpoint": API_FOOTBALL_TEAMS_NORMALIZER_ENDPOINT,
        "mode": API_FOOTBALL_TEAMS_NORMALIZER_MODE,
        "payload_hash": _stable_payload_hash(payload),
        "payload_top_level_keys": _top_level_keys(payload),
        "normalized_count": len(teams),
        "teams": teams,
        "db_writes": False,
        "prediction_created": False,
        "betting_created": False,
    }


def _response_items(
    payload: Mapping[str, Any],
    *,
    endpoint_label: str,
) -> list[object]:
    if not isinstance(payload, Mapping):
        raise ApiFootballLeaguesTeamsResponseNormalizationError(
            f"{endpoint_label} response payload must be a mapping."
        )

    response = payload.get("response", [])
    if not isinstance(response, list):
        raise ApiFootballLeaguesTeamsResponseNormalizationError(
            f"{endpoint_label} response payload 'response' must be a list."
        )
    return response


def _normalize_league_item(
    item: object,
) -> list[dict[str, NormalizedLeaguesTeamsValue | str]]:
    league_payload: Mapping[str, Any]
    if isinstance(item, Mapping):
        league_payload = item
    else:
        league_payload = {}

    seasons = league_payload.get("seasons", [])
    season_payloads = (
        [season for season in seasons if isinstance(season, Mapping)]
        if isinstance(seasons, list)
        else []
    )
    if not season_payloads:
        season_payloads = [{}]

    return [
        _normalize_league_season(league_payload, season_payload)
        for season_payload in season_payloads
    ]


def _normalize_league_season(
    league_payload: Mapping[str, Any],
    season_payload: Mapping[str, Any],
) -> dict[str, NormalizedLeaguesTeamsValue | str]:
    normalized: dict[str, NormalizedLeaguesTeamsValue | str] = {
        "provider": API_FOOTBALL_LEAGUES_TEAMS_NORMALIZER_PROVIDER
    }
    for output_field, path in API_FOOTBALL_LEAGUE_NORMALIZED_FIELDS:
        normalized[output_field] = _public_scalar(_get_nested(league_payload, path))
    for output_field, path in API_FOOTBALL_LEAGUE_SEASON_NORMALIZED_FIELDS:
        normalized[output_field] = _public_scalar(_get_nested(season_payload, path))
    return normalized


def _normalize_team_item(
    item: object,
) -> dict[str, NormalizedLeaguesTeamsValue | str]:
    team_payload: Mapping[str, Any]
    if isinstance(item, Mapping):
        team_payload = item
    else:
        team_payload = {}

    normalized: dict[str, NormalizedLeaguesTeamsValue | str] = {
        "provider": API_FOOTBALL_LEAGUES_TEAMS_NORMALIZER_PROVIDER
    }
    for output_field, path in API_FOOTBALL_TEAM_NORMALIZED_FIELDS:
        normalized[output_field] = _public_scalar(_get_nested(team_payload, path))
    return normalized


def _get_nested(payload: Mapping[str, Any], path: tuple[str, ...]) -> object:
    current: object = payload
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _public_scalar(value: object) -> NormalizedLeaguesTeamsValue:
    if value is None or isinstance(value, str | int | bool):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return None
    return None


def _top_level_keys(payload: Mapping[str, Any]) -> list[str]:
    return sorted(str(key) for key in payload)


def _stable_payload_hash(payload: Mapping[str, Any]) -> str:
    canonical_payload = _canonicalize(payload)
    serialized_payload = json.dumps(
        canonical_payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(serialized_payload.encode("utf-8")).hexdigest()


def _canonicalize(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, list | tuple):
        return [_canonicalize(item) for item in value]
    if value is None or isinstance(value, str | int | bool):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return repr(value)
    return repr(value)


__all__ = [
    "API_FOOTBALL_LEAGUES_NORMALIZER_ENDPOINT",
    "API_FOOTBALL_LEAGUES_NORMALIZER_MODE",
    "API_FOOTBALL_LEAGUES_TEAMS_NORMALIZER_PROVIDER",
    "API_FOOTBALL_TEAMS_NORMALIZER_ENDPOINT",
    "API_FOOTBALL_TEAMS_NORMALIZER_MODE",
    "ApiFootballLeaguesTeamsResponseNormalizationError",
    "normalize_api_football_leagues_response",
    "normalize_api_football_teams_response",
]
