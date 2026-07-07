from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Final

from app.modules.providers.api_football_fixture_request_builder import (
    build_api_football_fixture_read_only_request,
)
from app.modules.providers.api_football_fixture_response_normalizer import (
    normalize_api_football_fixture_response,
)


API_FOOTBALL_FIXTURE_HARNESS_TRANSPORT_LABEL: Final = "injected_test_transport"

FixtureReadOnlyTransport = Callable[[Mapping[str, object]], Mapping[str, Any]]


class ApiFootballFixtureReadOnlyHarnessError(RuntimeError):
    """Raised when the injected Phase 29 test transport cannot return safely."""


def run_api_football_fixture_read_only_harness(
    query: Mapping[str, object] | None,
    transport: FixtureReadOnlyTransport,
) -> dict[str, object]:
    if not callable(transport):
        raise ApiFootballFixtureReadOnlyHarnessError(
            "Fixture read-only harness requires an injected test transport."
        )

    fixture_request = build_api_football_fixture_read_only_request(query)
    request_summary = fixture_request.public_safe_summary()

    try:
        payload = transport(request_summary)
    except Exception as exc:
        raise ApiFootballFixtureReadOnlyHarnessError(
            "Injected test transport failed without exposing provider content."
        ) from exc

    normalized_response = normalize_api_football_fixture_response(payload)
    return {
        "provider": request_summary["provider"],
        "endpoint": request_summary["endpoint"],
        "method": request_summary["method"],
        "read_only": request_summary["read_only"],
        "request_query": request_summary["query"],
        "transport_used": API_FOOTBALL_FIXTURE_HARNESS_TRANSPORT_LABEL,
        "executed": True,
        "normalized_count": normalized_response["normalized_count"],
        "fixtures": normalized_response["fixtures"],
        "payload_hash": normalized_response["payload_hash"],
        "payload_top_level_keys": normalized_response["payload_top_level_keys"],
        "db_writes": False,
        "prediction_created": False,
        "betting_created": False,
    }
