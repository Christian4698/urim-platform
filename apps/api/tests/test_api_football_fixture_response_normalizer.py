from __future__ import annotations

import inspect
import json
import socket

import pytest

from app.modules.providers import api_football_fixture_response_normalizer as normalizer_module
from app.modules.providers.api_football_fixture_response_normalizer import (
    API_FOOTBALL_FIXTURE_NORMALIZER_ENDPOINT,
    API_FOOTBALL_FIXTURE_NORMALIZER_PROVIDER,
    ApiFootballFixtureResponseNormalizationError,
    normalize_api_football_fixture_response,
)


def _literal(*parts: str) -> str:
    return "".join(parts)


def _complete_fixture(fixture_id: int = 101) -> dict[str, object]:
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
            "home": {"id": 33, "name": "Home FC", "winner": None},
            "away": {"id": 34, "name": "Away FC", "winner": None},
        },
        "goals": {"home": 1, "away": 2},
        "score": {
            "halftime": {"home": 0, "away": 1},
            "fulltime": {"home": 1, "away": 2},
            "extratime": {"home": None, "away": None},
        },
        "ignored_provider_field": "must not be returned",
    }


def _payload_with_response(response: list[object]) -> dict[str, object]:
    return {
        "get": "fixtures",
        "parameters": {"league": "39", "season": "2026"},
        "errors": [],
        "results": len(response),
        "paging": {"current": 1, "total": 1},
        "response": response,
    }


def test_fixture_response_normalizer_normalizes_complete_fake_fixture() -> None:
    output = normalize_api_football_fixture_response(
        _payload_with_response([_complete_fixture()])
    )

    assert output["provider"] == API_FOOTBALL_FIXTURE_NORMALIZER_PROVIDER
    assert output["endpoint"] == API_FOOTBALL_FIXTURE_NORMALIZER_ENDPOINT
    assert output["read_only"] is True
    assert output["normalized_count"] == 1
    assert output["payload_top_level_keys"] == [
        "errors",
        "get",
        "paging",
        "parameters",
        "response",
        "results",
    ]
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


def test_fixture_response_normalizer_normalizes_multiple_fixtures() -> None:
    output = normalize_api_football_fixture_response(
        _payload_with_response([_complete_fixture(101), _complete_fixture(102)])
    )

    assert output["normalized_count"] == 2
    assert [fixture["provider_fixture_id"] for fixture in output["fixtures"]] == [
        101,
        102,
    ]


def test_fixture_response_normalizer_handles_empty_response() -> None:
    output = normalize_api_football_fixture_response(_payload_with_response([]))

    assert output["normalized_count"] == 0
    assert output["fixtures"] == []


def test_fixture_response_normalizer_uses_none_for_missing_nested_fields() -> None:
    output = normalize_api_football_fixture_response(
        _payload_with_response([{"fixture": {"id": 777}}])
    )

    assert output["normalized_count"] == 1
    assert output["fixtures"] == [
        {
            "provider": "api-football",
            "provider_fixture_id": 777,
            "provider_league_id": None,
            "provider_season": None,
            "fixture_date": None,
            "fixture_timezone": None,
            "fixture_status_short": None,
            "fixture_status_long": None,
            "home_team_provider_id": None,
            "home_team_name": None,
            "away_team_provider_id": None,
            "away_team_name": None,
            "goals_home": None,
            "goals_away": None,
            "score_halftime_home": None,
            "score_halftime_away": None,
            "score_fulltime_home": None,
            "score_fulltime_away": None,
        }
    ]


def test_fixture_response_normalizer_exposes_hash_without_provider_body() -> None:
    output = normalize_api_football_fixture_response(
        _payload_with_response([_complete_fixture()])
    )

    assert isinstance(output["payload_hash"], str)
    assert len(output["payload_hash"]) == 64
    assert "payload_top_level_keys" in output

    serialized = json.dumps(output, sort_keys=True)
    assert "ignored_provider_field" not in serialized
    assert "Ignored Stadium" not in serialized
    assert "Ignored League" not in serialized
    assert "extratime" not in serialized
    for fixture in output["fixtures"]:
        assert "fixture" not in fixture
        assert "league" not in fixture
        assert "teams" not in fixture
        assert "score" not in fixture


def test_fixture_response_normalizer_payload_hash_is_deterministic() -> None:
    payload_a = _payload_with_response([_complete_fixture()])
    payload_b = {
        "response": [_complete_fixture()],
        "paging": {"total": 1, "current": 1},
        "results": 1,
        "errors": [],
        "parameters": {"season": "2026", "league": "39"},
        "get": "fixtures",
    }
    changed_payload = _payload_with_response([_complete_fixture(202)])

    output_a = normalize_api_football_fixture_response(payload_a)
    output_b = normalize_api_football_fixture_response(payload_b)
    changed_output = normalize_api_football_fixture_response(changed_payload)

    assert output_a["payload_hash"] == output_b["payload_hash"]
    assert output_a["payload_hash"] != changed_output["payload_hash"]


def test_fixture_response_normalizer_does_not_use_network_or_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network must not be used")

    monkeypatch.setattr(socket, "create_connection", fail_network)

    output = normalize_api_football_fixture_response(
        _payload_with_response([_complete_fixture()])
    )

    assert output["normalized_count"] == 1


@pytest.mark.parametrize(
    "forbidden_field",
    ["odds", "bookmaker", "stake", "prediction", "betting"],
)
def test_fixture_response_normalizer_does_not_return_forbidden_fixture_fields(
    forbidden_field: str,
) -> None:
    output = normalize_api_football_fixture_response(
        _payload_with_response(
            [
                {
                    **_complete_fixture(),
                    forbidden_field: "must not be returned",
                }
            ]
        )
    )

    serialized_fixtures = json.dumps(output["fixtures"], sort_keys=True).lower()
    assert forbidden_field not in serialized_fixtures


def test_fixture_response_normalizer_rejects_non_mapping_payload() -> None:
    with pytest.raises(ApiFootballFixtureResponseNormalizationError):
        normalize_api_football_fixture_response(["response"])  # type: ignore[arg-type]


def test_fixture_response_normalizer_rejects_non_list_response() -> None:
    with pytest.raises(ApiFootballFixtureResponseNormalizationError, match="response"):
        normalize_api_football_fixture_response({"response": {}})


def test_fixture_response_normalizer_source_has_no_network_auth_or_url_material() -> None:
    module_source = inspect.getsource(normalizer_module)
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
        _literal('"', "fixture", '":'),
        _literal('"', "league", '":'),
        _literal('"', "teams", '":'),
    )
    for fragment in forbidden_fragments:
        assert fragment not in module_source_lower


def test_fixture_response_normalizer_doc_exists_and_documents_scope() -> None:
    repo_root = normalizer_module.__file__.split("apps")[0]
    doc_path = (
        f"{repo_root}docs/47_API_FOOTBALL_FIXTURE_RESPONSE_NORMALIZER.md"
    )

    with open(doc_path, encoding="utf-8") as doc_file:
        doc_text = doc_file.read()

    assert "Phase 28" in doc_text
    assert "fake/test-only" in doc_text
    assert "## No DB ingestion yet" in doc_text
    assert "## No prediction yet" in doc_text
    assert "## No betting/odds yet" in doc_text
    assert "payload brut" not in doc_text.lower()


def test_fixture_response_normalizer_index_references_phase_28_doc() -> None:
    repo_root = normalizer_module.__file__.split("apps")[0]
    index_path = f"{repo_root}docs/index.md"

    with open(index_path, encoding="utf-8") as index_file:
        index_text = index_file.read()

    assert "47_API_FOOTBALL_FIXTURE_RESPONSE_NORMALIZER.md" in index_text
