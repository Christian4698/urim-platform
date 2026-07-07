from __future__ import annotations

import inspect
import json
import socket

import pytest

from app.modules.providers import api_football_fixture_request_builder as builder_module
from app.modules.providers.api_football_fixture_request_builder import (
    API_FOOTBALL_FIXTURE_ALLOWED_QUERY_KEYS,
    API_FOOTBALL_FIXTURE_FORBIDDEN_QUERY_KEYS,
    API_FOOTBALL_FIXTURE_REQUEST_ENDPOINT,
    API_FOOTBALL_FIXTURE_REQUEST_METHOD,
    API_FOOTBALL_FIXTURE_REQUEST_PROVIDER,
    ApiFootballFixtureRequestValidationError,
    build_api_football_fixture_read_only_request,
)


def _literal(*parts: str) -> str:
    return "".join(parts)


def test_fixture_request_builder_builds_empty_public_safe_request() -> None:
    request = build_api_football_fixture_read_only_request()

    assert request.provider == API_FOOTBALL_FIXTURE_REQUEST_PROVIDER
    assert request.endpoint == API_FOOTBALL_FIXTURE_REQUEST_ENDPOINT
    assert request.method == API_FOOTBALL_FIXTURE_REQUEST_METHOD
    assert request.read_only is True
    assert dict(request.query) == {}
    assert request.db_writes is False
    assert request.prediction_requested is False
    assert request.betting_requested is False
    assert request.public_safe_summary() == {
        "provider": "api-football",
        "endpoint": "/fixtures",
        "method": "GET",
        "read_only": True,
        "query": {},
        "db_writes": False,
        "prediction_requested": False,
        "betting_requested": False,
    }


def test_fixture_request_builder_accepts_allowed_query_in_stable_order() -> None:
    request = build_api_football_fixture_read_only_request(
        {
            "status": " NS ",
            "timezone": " Africa/Kinshasa ",
            "to": "2026-07-31",
            "from": "2026-07-01",
            "date": "2026-07-07",
            "team": 33,
            "season": 2026,
            "league": 39,
        }
    )

    expected_query = {
        "league": 39,
        "season": 2026,
        "team": 33,
        "date": "2026-07-07",
        "from": "2026-07-01",
        "to": "2026-07-31",
        "timezone": "Africa/Kinshasa",
        "status": "NS",
    }
    assert list(request.query) == list(API_FOOTBALL_FIXTURE_ALLOWED_QUERY_KEYS)
    assert dict(request.query) == expected_query
    assert request.public_safe_summary()["query"] == expected_query


def test_fixture_request_builder_rejects_non_mapping_query() -> None:
    with pytest.raises(ApiFootballFixtureRequestValidationError):
        build_api_football_fixture_read_only_request(["league"])  # type: ignore[arg-type]


def test_fixture_request_builder_rejects_non_string_query_key() -> None:
    with pytest.raises(ApiFootballFixtureRequestValidationError):
        build_api_football_fixture_read_only_request({1: 39})  # type: ignore[dict-item]


@pytest.mark.parametrize("key", ["unknown", "fixture", "league_id"])
def test_fixture_request_builder_rejects_unknown_keys(key: str) -> None:
    with pytest.raises(ApiFootballFixtureRequestValidationError, match="Unknown"):
        build_api_football_fixture_read_only_request({key: "value"})


@pytest.mark.parametrize("key", API_FOOTBALL_FIXTURE_FORBIDDEN_QUERY_KEYS)
def test_fixture_request_builder_rejects_forbidden_keys(key: str) -> None:
    with pytest.raises(ApiFootballFixtureRequestValidationError, match="forbidden"):
        build_api_football_fixture_read_only_request({key: "value"})


@pytest.mark.parametrize("key", [" odds ", "Prediction", "BETTING"])
def test_fixture_request_builder_rejects_normalized_forbidden_keys(key: str) -> None:
    with pytest.raises(ApiFootballFixtureRequestValidationError, match="forbidden"):
        build_api_football_fixture_read_only_request({key: "value"})


@pytest.mark.parametrize("key", ["league", "team"])
@pytest.mark.parametrize("value", [0, -1, True, "1", 1.5, None])
def test_fixture_request_builder_rejects_invalid_positive_ints(
    key: str,
    value: object,
) -> None:
    with pytest.raises(ApiFootballFixtureRequestValidationError):
        build_api_football_fixture_read_only_request({key: value})


@pytest.mark.parametrize(
    "value",
    [0, -1, True, "2026", 2026.0, None, 1899, 2101, 999, 10000],
)
def test_fixture_request_builder_rejects_invalid_seasons(value: object) -> None:
    with pytest.raises(ApiFootballFixtureRequestValidationError):
        build_api_football_fixture_read_only_request({"season": value})


@pytest.mark.parametrize("key", ["date", "from", "to"])
@pytest.mark.parametrize(
    "value",
    ["2026/07/07", "2026-7-07", "2026-07-7", "2026-02-30", 20260707, None, True],
)
def test_fixture_request_builder_rejects_invalid_dates(
    key: str,
    value: object,
) -> None:
    with pytest.raises(ApiFootballFixtureRequestValidationError):
        build_api_football_fixture_read_only_request({key: value})


def test_fixture_request_builder_rejects_inverted_date_range() -> None:
    with pytest.raises(ApiFootballFixtureRequestValidationError, match="from"):
        build_api_football_fixture_read_only_request(
            {"from": "2026-07-31", "to": "2026-07-01"}
        )


@pytest.mark.parametrize("key", ["timezone", "status"])
@pytest.mark.parametrize("value", ["", "   ", 123, None, True])
def test_fixture_request_builder_rejects_blank_or_non_string_text_fields(
    key: str,
    value: object,
) -> None:
    with pytest.raises(ApiFootballFixtureRequestValidationError):
        build_api_football_fixture_read_only_request({key: value})


def test_fixture_request_builder_does_not_require_network_or_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network must not be used")

    monkeypatch.setattr(socket, "create_connection", fail_network)

    request = build_api_football_fixture_read_only_request({"league": 39})

    assert request.public_safe_summary()["query"] == {"league": 39}


def test_fixture_request_builder_source_has_no_network_auth_or_payload_material() -> None:
    module_source = inspect.getsource(builder_module)
    module_source_lower = module_source.lower()

    forbidden_fragments = (
        "requests",
        "httpx",
        "aiohttp",
        "urlopen",
        _literal("author", "ization"),
        _literal("bear", "er"),
        _literal("x", "-rapid", "api-key"),
        _literal("api-football", ".com"),
        _literal("api", "-sports"),
        _literal("rapid", "api"),
        _literal("raw", "_payload"),
        _literal('"', "response", '":'),
        _literal('"', "parameters", '":'),
    )
    for fragment in forbidden_fragments:
        assert fragment not in module_source_lower


def test_fixture_request_builder_public_summary_serializes_safely() -> None:
    request = build_api_football_fixture_read_only_request(
        {"league": 39, "season": 2026, "date": "2026-07-07"}
    )

    serialized = json.dumps(request.public_safe_summary(), sort_keys=True)
    serialized_lower = serialized.lower()

    safe_fragments = (
        '"db_writes": false',
        '"prediction_requested": false',
        '"betting_requested": false',
        '"read_only": true',
    )
    for fragment in safe_fragments:
        assert fragment in serialized_lower

    forbidden_fragments = (
        _literal("api", "key"),
        _literal("credential", "="),
        _literal("secret", "="),
        _literal("author", "ization"),
        _literal("bear", "er"),
        _literal("header", "s"),
        _literal("api-football", ".com"),
        _literal("raw", "_payload"),
        _literal("db_writes", '": true'),
        _literal("prediction_requested", '": true'),
        _literal("betting_requested", '": true'),
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized_lower
