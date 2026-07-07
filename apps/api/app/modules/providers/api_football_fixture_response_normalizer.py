from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import json
import math
from typing import Any, Final


API_FOOTBALL_FIXTURE_NORMALIZER_PROVIDER: Final = "api-football"
API_FOOTBALL_FIXTURE_NORMALIZER_ENDPOINT: Final = "/fixtures"

API_FOOTBALL_FIXTURE_NORMALIZED_FIELDS: Final = (
    ("provider_fixture_id", ("fixture", "id")),
    ("provider_league_id", ("league", "id")),
    ("provider_season", ("league", "season")),
    ("fixture_date", ("fixture", "date")),
    ("fixture_timezone", ("fixture", "timezone")),
    ("fixture_status_short", ("fixture", "status", "short")),
    ("fixture_status_long", ("fixture", "status", "long")),
    ("home_team_provider_id", ("teams", "home", "id")),
    ("home_team_name", ("teams", "home", "name")),
    ("away_team_provider_id", ("teams", "away", "id")),
    ("away_team_name", ("teams", "away", "name")),
    ("goals_home", ("goals", "home")),
    ("goals_away", ("goals", "away")),
    ("score_halftime_home", ("score", "halftime", "home")),
    ("score_halftime_away", ("score", "halftime", "away")),
    ("score_fulltime_home", ("score", "fulltime", "home")),
    ("score_fulltime_away", ("score", "fulltime", "away")),
)

NormalizedFixtureValue = str | int | float | bool | None


class ApiFootballFixtureResponseNormalizationError(ValueError):
    """Raised when a Phase 28 fixture payload is outside the safe test contract."""


def normalize_api_football_fixture_response(
    payload: Mapping[str, Any],
) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        raise ApiFootballFixtureResponseNormalizationError(
            "Fixture response payload must be a mapping."
        )

    response = payload.get("response", [])
    if not isinstance(response, list):
        raise ApiFootballFixtureResponseNormalizationError(
            "Fixture response payload 'response' must be a list."
        )

    fixtures = [_normalize_fixture(item) for item in response]
    return {
        "provider": API_FOOTBALL_FIXTURE_NORMALIZER_PROVIDER,
        "endpoint": API_FOOTBALL_FIXTURE_NORMALIZER_ENDPOINT,
        "read_only": True,
        "normalized_count": len(fixtures),
        "fixtures": fixtures,
        "payload_hash": _stable_payload_hash(payload),
        "payload_top_level_keys": _top_level_keys(payload),
        "db_writes": False,
        "prediction_created": False,
        "betting_created": False,
    }


def _normalize_fixture(item: object) -> dict[str, NormalizedFixtureValue | str]:
    fixture_payload: Mapping[str, Any]
    if isinstance(item, Mapping):
        fixture_payload = item
    else:
        fixture_payload = {}

    normalized: dict[str, NormalizedFixtureValue | str] = {
        "provider": API_FOOTBALL_FIXTURE_NORMALIZER_PROVIDER
    }
    for output_field, path in API_FOOTBALL_FIXTURE_NORMALIZED_FIELDS:
        normalized[output_field] = _public_scalar(_get_nested(fixture_payload, path))
    return normalized


def _get_nested(payload: Mapping[str, Any], path: tuple[str, ...]) -> object:
    current: object = payload
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _public_scalar(value: object) -> NormalizedFixtureValue:
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
