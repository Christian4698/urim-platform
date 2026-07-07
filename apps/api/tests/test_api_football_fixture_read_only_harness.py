from __future__ import annotations

from pathlib import Path
import inspect
import json
import socket

import pytest

from app.modules.providers import api_football_fixture_read_only_harness as harness_module
from app.modules.providers.api_football_fixture_read_only_harness import (
    API_FOOTBALL_FIXTURE_HARNESS_TRANSPORT_LABEL,
    ApiFootballFixtureReadOnlyHarnessError,
    run_api_football_fixture_read_only_harness,
)
from app.modules.providers.api_football_fixture_request_builder import (
    ApiFootballFixtureRequestValidationError,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "48_API_FOOTBALL_FIXTURE_READ_ONLY_TRANSPORT_HARNESS.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"


def _literal(*parts: str) -> str:
    return "".join(parts)


def _fake_fixture(fixture_id: int = 101) -> dict[str, object]:
    return {
        "fixture": {
            "id": fixture_id,
            "date": "2026-07-07T18:00:00+00:00",
            "timezone": "UTC",
            "status": {"short": "NS", "long": "Not Started"},
            "venue": {"name": "Ignored Stadium"},
        },
        "league": {"id": 39, "season": 2026, "name": "Ignored League"},
        "teams": {
            "home": {"id": 33, "name": "Home FC"},
            "away": {"id": 34, "name": "Away FC"},
        },
        "goals": {"home": 1, "away": 2},
        "score": {
            "halftime": {"home": 0, "away": 1},
            "fulltime": {"home": 1, "away": 2},
        },
        "ignored_provider_field": "must not be returned",
    }


def _fake_payload(response: list[object]) -> dict[str, object]:
    return {
        "get": "fixtures",
        "parameters": {"league": "39", "season": "2026"},
        "errors": [],
        "results": len(response),
        "paging": {"current": 1, "total": 1},
        "response": response,
    }


def test_fixture_read_only_harness_calls_builder_transport_and_normalizer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeBuiltRequest:
        def public_safe_summary(self) -> dict[str, object]:
            return {
                "provider": "api-football",
                "endpoint": "/fixtures",
                "method": "GET",
                "read_only": True,
                "query": {"league": 39},
                "db_writes": False,
                "prediction_requested": False,
                "betting_requested": False,
            }

    def fake_builder(query: object) -> FakeBuiltRequest:
        assert query == {"league": 39}
        calls.append("builder")
        return FakeBuiltRequest()

    def fake_transport(request_summary: object) -> dict[str, object]:
        assert request_summary == FakeBuiltRequest().public_safe_summary()
        calls.append("transport")
        return {"response": []}

    def fake_normalizer(payload: object) -> dict[str, object]:
        assert payload == {"response": []}
        calls.append("normalizer")
        return {
            "normalized_count": 0,
            "fixtures": [],
            "payload_hash": "0" * 64,
            "payload_top_level_keys": ["response"],
        }

    monkeypatch.setattr(
        harness_module,
        "build_api_football_fixture_read_only_request",
        fake_builder,
    )
    monkeypatch.setattr(
        harness_module,
        "normalize_api_football_fixture_response",
        fake_normalizer,
    )

    output = run_api_football_fixture_read_only_harness(
        {"league": 39},
        fake_transport,
    )

    assert calls == ["builder", "transport", "normalizer"]
    assert output["transport_used"] == API_FOOTBALL_FIXTURE_HARNESS_TRANSPORT_LABEL
    assert output["executed"] is True


def test_fixture_read_only_harness_returns_public_safe_normalized_response() -> None:
    captured_request: dict[str, object] = {}

    def fake_transport(request_summary: object) -> dict[str, object]:
        assert isinstance(request_summary, dict)
        captured_request.update(request_summary)
        return _fake_payload([_fake_fixture()])

    output = run_api_football_fixture_read_only_harness(
        {"league": 39, "season": 2026},
        fake_transport,
    )

    assert captured_request["provider"] == "api-football"
    assert captured_request["endpoint"] == "/fixtures"
    assert captured_request["method"] == "GET"
    assert captured_request["read_only"] is True
    assert captured_request["query"] == {"league": 39, "season": 2026}

    assert output["provider"] == "api-football"
    assert output["endpoint"] == "/fixtures"
    assert output["method"] == "GET"
    assert output["read_only"] is True
    assert output["request_query"] == {"league": 39, "season": 2026}
    assert output["transport_used"] == "injected_test_transport"
    assert output["executed"] is True
    assert output["normalized_count"] == 1
    assert output["payload_top_level_keys"] == [
        "errors",
        "get",
        "paging",
        "parameters",
        "response",
        "results",
    ]
    assert isinstance(output["payload_hash"], str)
    assert len(output["payload_hash"]) == 64
    assert output["db_writes"] is False
    assert output["prediction_created"] is False
    assert output["betting_created"] is False

    assert output["fixtures"] == [
        {
            "provider": "api-football",
            "provider_fixture_id": 101,
            "provider_league_id": 39,
            "provider_season": 2026,
            "fixture_date": "2026-07-07T18:00:00+00:00",
            "fixture_timezone": "UTC",
            "fixture_status_short": "NS",
            "fixture_status_long": "Not Started",
            "home_team_provider_id": 33,
            "home_team_name": "Home FC",
            "away_team_provider_id": 34,
            "away_team_name": "Away FC",
            "goals_home": 1,
            "goals_away": 2,
            "score_halftime_home": 0,
            "score_halftime_away": 1,
            "score_fulltime_home": 1,
            "score_fulltime_away": 2,
        }
    ]


def test_fixture_read_only_harness_does_not_return_provider_body() -> None:
    output = run_api_football_fixture_read_only_harness(
        {"league": 39},
        lambda _request: _fake_payload([_fake_fixture()]),
    )

    serialized = json.dumps(output, sort_keys=True)
    assert "Ignored Stadium" not in serialized
    assert "Ignored League" not in serialized
    assert "ignored_provider_field" not in serialized


@pytest.mark.parametrize("key", ["unknown", "fixture", "league_id"])
def test_fixture_read_only_harness_rejects_unknown_query_params(key: str) -> None:
    def fail_transport(_request: object) -> dict[str, object]:
        raise AssertionError("transport must not be called")

    with pytest.raises(ApiFootballFixtureRequestValidationError):
        run_api_football_fixture_read_only_harness({key: "value"}, fail_transport)


@pytest.mark.parametrize(
    "key",
    ["odds", "predictions", "bookmaker", "stake", "betting"],
)
def test_fixture_read_only_harness_rejects_forbidden_query_params(key: str) -> None:
    def fail_transport(_request: object) -> dict[str, object]:
        raise AssertionError("transport must not be called")

    with pytest.raises(ApiFootballFixtureRequestValidationError):
        run_api_football_fixture_read_only_harness({key: "value"}, fail_transport)


def test_fixture_read_only_harness_does_not_require_network_or_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network must not be used")

    monkeypatch.setattr(socket, "create_connection", fail_network)

    output = run_api_football_fixture_read_only_harness(
        {"date": "2026-07-07"},
        lambda _request: _fake_payload([]),
    )

    assert output["executed"] is True
    assert output["normalized_count"] == 0


def test_fixture_read_only_harness_handles_empty_response() -> None:
    output = run_api_football_fixture_read_only_harness(
        {"league": 39},
        lambda _request: _fake_payload([]),
    )

    assert output["executed"] is True
    assert output["normalized_count"] == 0
    assert output["fixtures"] == []


def test_fixture_read_only_harness_handles_transport_error_safely() -> None:
    def failing_transport(_request: object) -> dict[str, object]:
        raise RuntimeError("provider body details must not surface")

    with pytest.raises(ApiFootballFixtureReadOnlyHarnessError) as exc_info:
        run_api_football_fixture_read_only_harness({"league": 39}, failing_transport)

    error_text = str(exc_info.value)
    assert "Injected test transport failed" in error_text
    assert "details must not surface" not in error_text


def test_fixture_read_only_harness_rejects_non_callable_transport() -> None:
    with pytest.raises(ApiFootballFixtureReadOnlyHarnessError):
        run_api_football_fixture_read_only_harness(
            {"league": 39},
            None,  # type: ignore[arg-type]
        )


def test_fixture_read_only_harness_source_has_no_network_auth_or_url_material() -> None:
    module_source = inspect.getsource(harness_module)
    module_source_lower = module_source.lower()

    forbidden_fragments = (
        _literal("request", "s"),
        _literal("http", "x"),
        _literal("aio", "http"),
        "urlopen",
        _literal("url", "lib"),
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


def test_fixture_read_only_harness_serialized_output_has_no_activation_flags() -> None:
    output = run_api_football_fixture_read_only_harness(
        {"league": 39},
        lambda _request: _fake_payload([_fake_fixture()]),
    )
    serialized = json.dumps(output, sort_keys=True).lower()

    safe_fragments = (
        '"db_writes": false',
        '"prediction_created": false',
        '"betting_created": false',
        '"read_only": true',
    )
    for fragment in safe_fragments:
        assert fragment in serialized

    forbidden_fragments = (
        _literal("api", "key"),
        _literal("credential", "="),
        _literal("secret", "="),
        _literal("author", "ization"),
        _literal("bear", "er"),
        _literal("header", "s"),
        _literal("api-football", ".com"),
        _literal("db_writes", '": true'),
        _literal("prediction_created", '": true'),
        _literal("betting_created", '": true'),
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized


def test_fixture_read_only_harness_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")

    assert "Phase 29" in doc_text
    assert "fake/test-only" in doc_text
    assert "## No real API call" in doc_text
    assert "## No DB ingestion" in doc_text
    assert "## No prediction" in doc_text
    assert "## No betting/odds" in doc_text


def test_fixture_read_only_harness_index_references_phase_29_doc() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "48_API_FOOTBALL_FIXTURE_READ_ONLY_TRANSPORT_HARNESS.md" in index_text
