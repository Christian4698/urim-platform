from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import sys
from typing import Any, Final
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.modules.providers.api_football_fixture_response_normalizer import (  # noqa: E402
    normalize_api_football_fixture_response,
)
from scripts.api_football_fixture_local_real_smoke_protocol import (  # noqa: E402
    FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES,
    run_api_football_fixture_local_real_smoke_protocol,
)


def _literal(*parts: str) -> str:
    return "".join(parts)


FIXTURE_FIRST_REAL_LOCAL_SMOKE_PROVIDER: Final = "api-football"
FIXTURE_FIRST_REAL_LOCAL_SMOKE_ENDPOINT: Final = "/fixtures"
FIXTURE_FIRST_REAL_LOCAL_SMOKE_MODE: Final = "fixture_first_real_local_smoke_only"
FIXTURE_FIRST_REAL_LOCAL_SMOKE_NOT_READY_STATUS: Final = (
    "not_ready_for_fixture_first_real_local_smoke"
)
FIXTURE_FIRST_REAL_LOCAL_SMOKE_COMPLETED_STATUS: Final = (
    "completed_fixture_first_real_local_smoke"
)
FIXTURE_FIRST_REAL_LOCAL_SMOKE_PROVIDER_HTTP_ERROR_STATUS: Final = "provider_http_error"
FIXTURE_FIRST_REAL_LOCAL_SMOKE_REQUEST_FAILED_STATUS: Final = "request_execution_failed"
FIXTURE_FIRST_REAL_LOCAL_SMOKE_NORMALIZATION_FAILED_STATUS: Final = (
    "normalization_failed"
)

FIXTURE_FIRST_REAL_LOCAL_SMOKE_AUTH_ENV: Final = (
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_AUTH"
)
FIXTURE_FIRST_REAL_LOCAL_SMOKE_BASE_URL_ENV: Final = (
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_BASE_URL"
)
FIXTURE_FIRST_REAL_LOCAL_SMOKE_ENV_NAMES: Final = (
    *FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES,
    FIXTURE_FIRST_REAL_LOCAL_SMOKE_AUTH_ENV,
    FIXTURE_FIRST_REAL_LOCAL_SMOKE_BASE_URL_ENV,
)
FIXTURE_FIRST_REAL_LOCAL_SMOKE_ALLOWED_AUTH_HEADER: Final = "x-apisports-key"

_FORBIDDEN_ENDPOINT_REFERENCES: Final = (
    "/predictions",
    "/odds",
)
_FORBIDDEN_OUTPUT_FRAGMENTS: Final = (
    _literal("api", "_key"),
    _literal("author", "ization"),
    _literal("bear", "er"),
    "credential",
    _literal("provider", "_credentials"),
    "password",
    "secret",
    "token",
    _literal("http", "://"),
    _literal("https", "://"),
    _literal("api-football", ".com"),
    _literal("api", "-sports"),
    _literal("rapid", "api"),
    _literal("x", "-rapid", "api"),
    _literal("raw", "_payload"),
    _literal("smoke", "_payload"),
    _literal('"', "fixtures", '":'),
    _literal("provider", "_fixture_id"),
    _literal("home", "_team_provider_id"),
    _literal("away", "_team_provider_id"),
    _literal("home", "_team_name"),
    _literal("away", "_team_name"),
    _literal("goals", "_home"),
    _literal("goals", "_away"),
    _literal("score", "_halftime_home"),
    _literal("score", "_halftime_away"),
    _literal("score", "_fulltime_home"),
    _literal("score", "_fulltime_away"),
)

FixtureRequestCallable = Callable[[str, str, Mapping[str, str]], Mapping[str, Any]]


class ApiFootballFixtureFirstRealLocalSmokeError(RuntimeError):
    """Raised when a fixture real smoke result would not be public-safe."""


@dataclass(frozen=True)
class ApiFootballFixtureFirstRealLocalSmokeResult:
    status: str = FIXTURE_FIRST_REAL_LOCAL_SMOKE_NOT_READY_STATUS
    executed: bool = False
    provider: str = FIXTURE_FIRST_REAL_LOCAL_SMOKE_PROVIDER
    endpoint: str = FIXTURE_FIRST_REAL_LOCAL_SMOKE_ENDPOINT
    mode: str = FIXTURE_FIRST_REAL_LOCAL_SMOKE_MODE
    request_query: Mapping[str, str] | None = None
    normalized_count: int | None = None
    payload_hash: str | None = None
    payload_top_level_keys: tuple[str, ...] = ()
    http_status: int | None = None
    db_writes: bool = False
    prediction_created: bool = False
    betting_created: bool = False
    blocking_reasons: tuple[str, ...] = ()

    def public_safe_summary(self) -> dict[str, Any]:
        summary = asdict(self)
        if self.request_query is None:
            summary.pop("request_query")
        else:
            summary["request_query"] = dict(self.request_query)
        if self.normalized_count is None:
            summary.pop("normalized_count")
        if self.payload_hash is None:
            summary.pop("payload_hash")
        if self.payload_top_level_keys:
            summary["payload_top_level_keys"] = list(self.payload_top_level_keys)
        else:
            summary.pop("payload_top_level_keys")
        if self.http_status is None:
            summary.pop("http_status")
        if self.blocking_reasons:
            summary["blocking_reasons"] = list(self.blocking_reasons)
        else:
            summary.pop("blocking_reasons")
        return summary


def run_api_football_fixture_first_real_local_smoke(
    *,
    environ: Mapping[str, str] | None = None,
    request_callable: FixtureRequestCallable | None = None,
) -> ApiFootballFixtureFirstRealLocalSmokeResult:
    environment = os.environ if environ is None else environ
    protocol = run_api_football_fixture_local_real_smoke_protocol(environ=environment)
    blocking_reasons = list(protocol.blocking_reasons)

    auth_material = environment.get(FIXTURE_FIRST_REAL_LOCAL_SMOKE_AUTH_ENV, "").strip()
    base_url = environment.get(FIXTURE_FIRST_REAL_LOCAL_SMOKE_BASE_URL_ENV, "").strip()
    if not auth_material:
        blocking_reasons.append("local_auth_material_missing")
    if not base_url:
        blocking_reasons.append("local_provider_reference_missing")
    elif _contains_forbidden_endpoint_reference(base_url):
        blocking_reasons.append("forbidden_provider_endpoint_reference")

    approved_query = dict(protocol.approved_query or {})
    if not protocol.ready_for_fixture_real_smoke:
        blocking_reasons.append("fixture_protocol_not_ready")

    if blocking_reasons:
        return _validated_result(
            ApiFootballFixtureFirstRealLocalSmokeResult(
                blocking_reasons=tuple(_dedupe(blocking_reasons)),
            ),
            environ=environment,
        )

    effective_callable = request_callable or _standard_library_fixture_get_request
    try:
        payload = effective_callable(base_url, auth_material, approved_query)
    except HTTPError as exc:
        return _validated_result(
            ApiFootballFixtureFirstRealLocalSmokeResult(
                status=FIXTURE_FIRST_REAL_LOCAL_SMOKE_PROVIDER_HTTP_ERROR_STATUS,
                http_status=exc.code,
                blocking_reasons=("provider_http_error",),
            ),
            environ=environment,
        )
    except Exception:
        return _validated_result(
            ApiFootballFixtureFirstRealLocalSmokeResult(
                status=FIXTURE_FIRST_REAL_LOCAL_SMOKE_REQUEST_FAILED_STATUS,
                blocking_reasons=("request_execution_failed",),
            ),
            environ=environment,
        )

    try:
        normalized_response = normalize_api_football_fixture_response(payload)
    except Exception:
        return _validated_result(
            ApiFootballFixtureFirstRealLocalSmokeResult(
                status=FIXTURE_FIRST_REAL_LOCAL_SMOKE_NORMALIZATION_FAILED_STATUS,
                blocking_reasons=("normalization_failed",),
            ),
            environ=environment,
        )

    result = ApiFootballFixtureFirstRealLocalSmokeResult(
        status=FIXTURE_FIRST_REAL_LOCAL_SMOKE_COMPLETED_STATUS,
        executed=True,
        request_query=approved_query,
        normalized_count=int(normalized_response["normalized_count"]),
        payload_hash=str(normalized_response["payload_hash"]),
        payload_top_level_keys=tuple(normalized_response["payload_top_level_keys"]),
    )
    return _validated_result(result, environ=environment)


def assert_api_football_fixture_first_real_local_smoke_output_safe(
    result: ApiFootballFixtureFirstRealLocalSmokeResult,
    *,
    environ: Mapping[str, str] | None = None,
) -> None:
    _assert_output_safe(result, environ=environ)


def main() -> int:
    result = run_api_football_fixture_first_real_local_smoke(environ=os.environ)
    print(json.dumps(result.public_safe_summary(), sort_keys=True))
    return 0


def _standard_library_fixture_get_request(
    base_url: str,
    auth_material: str,
    query: Mapping[str, str],
) -> Mapping[str, Any]:
    target = base_url
    if query:
        separator = "&" if "?" in target else "?"
        target = f"{target}{separator}{urlencode(query)}"

    request = Request(target, method="GET")
    request.headers["Accept"] = "application/json"
    request.headers[FIXTURE_FIRST_REAL_LOCAL_SMOKE_ALLOWED_AUTH_HEADER] = auth_material
    with urlopen(request, timeout=10) as response:
        payload_bytes = response.read()
    payload = json.loads(payload_bytes.decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise ApiFootballFixtureFirstRealLocalSmokeError(
            "fixture first real local smoke response must be a JSON object"
        )
    return payload


def _validated_result(
    result: ApiFootballFixtureFirstRealLocalSmokeResult,
    *,
    environ: Mapping[str, str] | None,
) -> ApiFootballFixtureFirstRealLocalSmokeResult:
    _assert_output_safe(result, environ=environ)
    return result


def _assert_output_safe(
    result: ApiFootballFixtureFirstRealLocalSmokeResult,
    *,
    environ: Mapping[str, str] | None,
) -> None:
    environment = {} if environ is None else environ
    serialized_result = json.dumps(
        result.public_safe_summary(),
        default=str,
        sort_keys=True,
    ).lower()
    forbidden_fragments = set(_FORBIDDEN_OUTPUT_FRAGMENTS)
    forbidden_fragments.update(
        env_name.lower() for env_name in FIXTURE_FIRST_REAL_LOCAL_SMOKE_ENV_NAMES
    )
    auth_material = environment.get(FIXTURE_FIRST_REAL_LOCAL_SMOKE_AUTH_ENV, "").strip()
    base_url = environment.get(FIXTURE_FIRST_REAL_LOCAL_SMOKE_BASE_URL_ENV, "").strip()
    if auth_material:
        forbidden_fragments.add(auth_material.lower())
    if base_url:
        forbidden_fragments.add(base_url.lower())

    if any(fragment and fragment in serialized_result for fragment in forbidden_fragments):
        raise ApiFootballFixtureFirstRealLocalSmokeError(
            "fixture first real local smoke output contains non-public provider material"
        )


def _contains_forbidden_endpoint_reference(base_url: str) -> bool:
    normalized_base_url = base_url.lower()
    return any(fragment in normalized_base_url for fragment in _FORBIDDEN_ENDPOINT_REFERENCES)


def _dedupe(values: list[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return tuple(deduped)


if __name__ == "__main__":
    raise SystemExit(main())
