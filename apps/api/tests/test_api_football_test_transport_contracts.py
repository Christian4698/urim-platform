from collections.abc import Callable
from datetime import datetime
import json
from pathlib import Path
import socket

import pytest
from pydantic import ValidationError

import app.modules.providers.api_football_adapter as adapter_module
import app.modules.providers.api_football_transport as transport_module
from app.modules.providers.api_football_adapter import (
    ApiFootballProviderDisabledError,
    ApiFootballReadOnlyAdapter,
)
from app.modules.providers.api_football_transport import (
    API_FOOTBALL_RESPONSE_KINDS,
    API_FOOTBALL_TEST_PROVIDER_NAME,
    DEMO_NON_PROD_MARKER,
    PLACEHOLDER_MARKER,
    TEST_ONLY_MARKER,
    ApiFootballFixtureResponse,
    ApiFootballTestTransport,
    ApiFootballTransportProtocol,
    ApiFootballTransportResponse,
    stable_raw_hash,
)
from tests.helpers.payload_helpers import walk_keys, walk_values


def collect_responses(transport: ApiFootballTestTransport) -> list[ApiFootballTransportResponse]:
    return [
        transport.fetch_fixtures(),
        transport.fetch_results(),
        transport.fetch_team_statistics(),
        transport.fetch_standings(),
        transport.fetch_lineups(),
        transport.fetch_events(),
    ]


def test_api_football_test_transport_is_test_only() -> None:
    transport = ApiFootballTestTransport()

    assert isinstance(transport, ApiFootballTransportProtocol)
    assert transport.test_only is True
    assert transport.demo_non_prod is True
    assert transport.network_calls_enabled is False
    assert transport.db_ingestion_enabled is False
    assert transport.prediction_creation_enabled is False
    assert transport.betting_enabled is False

    for response in collect_responses(transport):
        assert response.payload_marker == TEST_ONLY_MARKER
        assert response.environment_marker == DEMO_NON_PROD_MARKER
        assert response.provider_name == API_FOOTBALL_TEST_PROVIDER_NAME
        assert TEST_ONLY_MARKER in response.quality_flags
        assert DEMO_NON_PROD_MARKER in response.quality_flags
        assert PLACEHOLDER_MARKER in response.quality_flags


def test_api_football_test_transport_does_not_touch_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_create_connection(*args: object, **kwargs: object) -> None:
        raise AssertionError("API-Football test transport must not touch sockets")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    transport = ApiFootballTestTransport()
    adapter = ApiFootballReadOnlyAdapter(transport=transport, allow_test_transport=True)

    assert collect_responses(transport)
    assert adapter.fetch_fixtures()
    assert adapter.fetch_results()
    assert adapter.fetch_team_statistics()
    assert adapter.fetch_standings()
    assert adapter.fetch_lineups()
    assert adapter.fetch_events()


def test_api_football_provider_modules_do_not_import_http_clients() -> None:
    forbidden_imports = (
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "import aiohttp",
        "from aiohttp",
    )

    for module in (transport_module, adapter_module):
        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden_import in forbidden_imports:
            assert forbidden_import not in source


def test_api_football_test_payloads_are_placeholders_only() -> None:
    forbidden_keys = {
        "score",
        "scores",
        "winner",
        "odds",
        "bookmaker",
        "bookmakers",
        "stake",
        "api_key",
        "token",
        "authorization",
        "secret",
        "password",
        "bearer",
        "credential",
        "provider_credentials",
    }
    forbidden_values = {
        "api-football.com",
        "api-sports",
        "rapidapi",
        "x-rapidapi",
        "Manchester",
        "Real Madrid",
        "Barcelona",
        "PSG",
        "Liverpool",
        "Chelsea",
        "Bayern",
        "Juventus",
        "Premier League",
        "Champions League",
    }

    responses = collect_responses(ApiFootballTestTransport())

    assert [response.response_kind for response in responses] == list(API_FOOTBALL_RESPONSE_KINDS)
    for response in responses:
        payload = response.model_dump(mode="json")
        serialized = json.dumps(payload)

        assert "PLACEHOLDER" in serialized
        assert forbidden_keys.isdisjoint(set(walk_keys(payload)))
        assert "http://" not in serialized.lower()
        assert "https://" not in serialized.lower()
        for value in walk_values(payload):
            if isinstance(value, str):
                assert not any(forbidden_value in value for forbidden_value in forbidden_values)


def test_api_football_test_payload_hashes_and_timestamps_are_stable() -> None:
    first_responses = collect_responses(ApiFootballTestTransport())
    second_responses = collect_responses(ApiFootballTestTransport())

    for first_response, second_response in zip(first_responses, second_responses, strict=True):
        assert first_response.raw_hash == stable_raw_hash(first_response.hash_source())
        assert first_response.raw_hash == second_response.raw_hash
        assert first_response.observed_at.tzinfo is not None
        assert first_response.available_at.tzinfo is not None
        assert first_response.fetched_at.tzinfo is not None
        assert first_response.observed_at <= first_response.available_at <= first_response.fetched_at


def test_api_football_test_transport_validators_reject_unsafe_payloads() -> None:
    safe_response = ApiFootballTestTransport().fetch_fixtures()

    missing_marker_payload = safe_response.hash_source()
    missing_marker_payload["quality_flags"] = [DEMO_NON_PROD_MARKER, PLACEHOLDER_MARKER]
    missing_marker_payload["raw_hash"] = stable_raw_hash(missing_marker_payload)
    with pytest.raises(ValidationError, match="TEST_ONLY"):
        ApiFootballFixtureResponse(**missing_marker_payload)

    production_data_payload = safe_response.hash_source()
    production_data_payload["data"] = {"score": "PLACEHOLDER_SCORE_NOT_ALLOWED"}
    production_data_payload["raw_hash"] = stable_raw_hash(production_data_payload)
    with pytest.raises(ValidationError, match="production sports data"):
        ApiFootballFixtureResponse(**production_data_payload)

    naive_timestamp_payload = safe_response.hash_source()
    naive_timestamp_payload["fetched_at"] = datetime(2026, 1, 1, 8, 10)
    naive_timestamp_payload["raw_hash"] = stable_raw_hash(naive_timestamp_payload)
    with pytest.raises(ValidationError, match="timezone-aware"):
        ApiFootballFixtureResponse(**naive_timestamp_payload)

    credential_payload = safe_response.hash_source()
    credential_payload["data"] = {"api_key": "DEMO_NON_PROD_FAKE_VALUE"}
    credential_payload["raw_hash"] = stable_raw_hash(credential_payload)
    with pytest.raises(ValidationError, match="credential"):
        ApiFootballFixtureResponse(**credential_payload)


@pytest.mark.parametrize(
    "operation",
    [
        lambda adapter: adapter.fetch_fixtures({"scope": "PLACEHOLDER_ONLY"}),
        lambda adapter: adapter.fetch_results({"scope": "PLACEHOLDER_ONLY"}),
        lambda adapter: adapter.fetch_team_statistics({"scope": "PLACEHOLDER_ONLY"}),
        lambda adapter: adapter.fetch_standings({"scope": "PLACEHOLDER_ONLY"}),
        lambda adapter: adapter.fetch_lineups({"scope": "PLACEHOLDER_ONLY"}),
        lambda adapter: adapter.fetch_events({"scope": "PLACEHOLDER_ONLY"}),
    ],
)
def test_api_football_adapter_stays_disabled_without_test_opt_in(
    operation: Callable[[ApiFootballReadOnlyAdapter], object],
) -> None:
    with pytest.raises(ApiFootballProviderDisabledError, match="disabled until provider activation gate"):
        operation(ApiFootballReadOnlyAdapter())

    with pytest.raises(ApiFootballProviderDisabledError, match="disabled until provider activation gate"):
        operation(ApiFootballReadOnlyAdapter(transport=ApiFootballTestTransport()))


def test_api_football_adapter_transforms_test_only_responses_to_observations() -> None:
    adapter = ApiFootballReadOnlyAdapter(
        transport=ApiFootballTestTransport(),
        allow_test_transport=True,
    )
    observations = [
        *adapter.fetch_fixtures(),
        *adapter.fetch_results(),
        *adapter.fetch_team_statistics(),
        *adapter.fetch_standings(),
        *adapter.fetch_lineups(),
        *adapter.fetch_events(),
    ]

    assert len(observations) == len(API_FOOTBALL_RESPONSE_KINDS)
    for observation, response_kind in zip(observations, API_FOOTBALL_RESPONSE_KINDS, strict=True):
        assert observation.provider == API_FOOTBALL_TEST_PROVIDER_NAME
        assert observation.provider_event_id.startswith("PLACEHOLDER_API_FOOTBALL_")
        assert observation.observed_at.tzinfo is not None
        assert observation.available_at.tzinfo is not None
        assert observation.fetched_at.tzinfo is not None
        assert observation.observed_at <= observation.available_at <= observation.fetched_at
        assert TEST_ONLY_MARKER in observation.quality_flags
        assert DEMO_NON_PROD_MARKER in observation.quality_flags
        assert PLACEHOLDER_MARKER in observation.quality_flags
        assert observation.raw_payload_ref is not None
        assert observation.raw_payload_ref.endpoint is None
        assert observation.raw_payload_ref.storage_uri is None
        assert observation.raw_payload_ref.raw_hash == observation.raw_hash
        assert observation.raw_payload_ref.metadata["payload_location"] == "in_memory_api_football_test_transport"
        assert observation.raw_payload_ref.metadata["response_kind"] == response_kind
        assert observation.data["response_kind"] == response_kind
        assert observation.data["payload_marker"] == TEST_ONLY_MARKER
        assert observation.data["environment_marker"] == DEMO_NON_PROD_MARKER
