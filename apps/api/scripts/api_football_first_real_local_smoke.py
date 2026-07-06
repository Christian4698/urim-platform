import json
import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.modules.providers.activation_readiness_final_gate import build_provider_activation_readiness_final_gate  # noqa: E402
from app.modules.providers.api_football_smoke_client import (  # noqa: E402
    API_FOOTBALL_SMOKE_ENV_NAMES,
    ApiFootballSmokeDisabledError,
    load_api_football_smoke_config,
)
from scripts.api_football_local_preflight import (  # noqa: E402
    LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES,
    LocalApiFootballPreflightRepoChecks,
    run_local_api_football_secret_env_preflight,
)
from scripts.api_football_local_smoke_harness import (  # noqa: E402
    LOCAL_HTTP_SMOKE_COMPLETED_STATUS,
    LOCAL_HTTP_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS,
    run_local_api_football_http_smoke_harness,
)

FIRST_REAL_LOCAL_SMOKE_PROVIDER = "api-football"
FIRST_REAL_LOCAL_SMOKE_MODE = "first_real_local_smoke_only"
FIRST_REAL_LOCAL_SMOKE_NOT_READY_STATUS = "not_ready_for_first_real_local_smoke"
FIRST_REAL_LOCAL_SMOKE_COMPLETED_STATUS = "completed_first_real_local_smoke"
FIRST_REAL_LOCAL_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS = "refused_unsafe_first_real_local_smoke_output"
FIRST_REAL_LOCAL_SMOKE_PROVIDER_HTTP_ERROR_STATUS = "provider_http_error"

FIRST_REAL_LOCAL_SMOKE_FORBIDDEN_OUTPUT_FRAGMENTS = (
    "api_key",
    "authorization",
    "bearer",
    "credential",
    "provider_credentials",
    "password",
    "secret",
    "token",
    "http://",
    "https://",
    "api-football.com",
    "api-sports",
    "rapidapi",
    "x-rapidapi",
    "raw_payload",
    "smoke_payload",
)

RequestCallable = Callable[[str, str, Mapping[str, Any] | None], Mapping[str, Any]]


@dataclass(frozen=True)
class ApiFootballFirstRealLocalSmokeResult:
    status: str = FIRST_REAL_LOCAL_SMOKE_NOT_READY_STATUS
    executed: bool = False
    provider: str = FIRST_REAL_LOCAL_SMOKE_PROVIDER
    mode: str = FIRST_REAL_LOCAL_SMOKE_MODE
    payload_hash: str | None = None
    payload_top_level_keys: tuple[str, ...] = ()
    http_status: int | None = None
    db_writes: bool = False
    prediction_created: bool = False
    betting_created: bool = False
    blocking_reasons: tuple[str, ...] = ()

    def public_safe_summary(self) -> dict[str, Any]:
        summary = asdict(self)
        summary["payload_top_level_keys"] = list(self.payload_top_level_keys)
        if self.http_status is None:
            summary.pop("http_status")
        if self.blocking_reasons:
            summary["blocking_reasons"] = list(self.blocking_reasons)
        else:
            summary.pop("blocking_reasons")
        return summary


class _TopLevelKeyRecordingCallable:
    def __init__(self, request_callable: RequestCallable) -> None:
        self._request_callable = request_callable
        self.payload_top_level_keys: tuple[str, ...] = ()

    def __call__(
        self,
        base_url: str,
        auth_material: str,
        query: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        payload = dict(self._request_callable(base_url, auth_material, query))
        self.payload_top_level_keys = tuple(sorted(str(key) for key in payload))
        return payload


def run_api_football_first_real_local_smoke(
    *,
    environ: Mapping[str, str] | None = None,
    request_callable: RequestCallable | None = None,
    repo_checks: Mapping[str, bool] | LocalApiFootballPreflightRepoChecks | None = None,
    query: Mapping[str, Any] | None = None,
) -> ApiFootballFirstRealLocalSmokeResult:
    environment = os.environ if environ is None else environ
    preflight = run_local_api_football_secret_env_preflight(
        environ=environment,
        repo_checks=repo_checks,
    )
    config = load_api_football_smoke_config(environment)

    blocking_reasons = list(preflight.blocking_reasons)
    if not config.non_production_confirmed:
        blocking_reasons.append("non_production_confirmation_missing")
    if not preflight.git_status_clean_recommended:
        blocking_reasons.append("git_status_not_clean")
    if not _provider_gate_blocked():
        blocking_reasons.append("provider_activation_gate_not_blocked")

    if blocking_reasons:
        return _validated_result(
            ApiFootballFirstRealLocalSmokeResult(blocking_reasons=tuple(blocking_reasons)),
            environ=environment,
        )

    effective_callable = request_callable or _standard_library_json_get_request_callable
    recording_callable = _TopLevelKeyRecordingCallable(effective_callable)
    try:
        harness_result = run_local_api_football_http_smoke_harness(
            request_callable=recording_callable,
            environ=environment,
            query=query,
        )
    except HTTPError as exc:
        return _validated_result(
            ApiFootballFirstRealLocalSmokeResult(
                status=FIRST_REAL_LOCAL_SMOKE_PROVIDER_HTTP_ERROR_STATUS,
                http_status=exc.code,
            ),
            environ=environment,
        )

    if harness_result.status == LOCAL_HTTP_SMOKE_COMPLETED_STATUS and harness_result.executed:
        result = ApiFootballFirstRealLocalSmokeResult(
            status=FIRST_REAL_LOCAL_SMOKE_COMPLETED_STATUS,
            executed=True,
            payload_hash=harness_result.payload_hash,
            payload_top_level_keys=recording_callable.payload_top_level_keys,
        )
    elif harness_result.status == LOCAL_HTTP_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS:
        result = ApiFootballFirstRealLocalSmokeResult(
            status=FIRST_REAL_LOCAL_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS,
            blocking_reasons=("unsafe_harness_output_refused",),
        )
    else:
        result = ApiFootballFirstRealLocalSmokeResult(
            blocking_reasons=("harness_execution_refused",),
        )

    return _validated_result(result, environ=environment)


def assert_api_football_first_real_local_smoke_output_safe(
    result: ApiFootballFirstRealLocalSmokeResult,
    *,
    environ: Mapping[str, str] | None = None,
) -> None:
    _assert_output_safe(result, environ=environ)


def main() -> int:
    result = run_api_football_first_real_local_smoke(environ=os.environ)
    print(json.dumps(result.public_safe_summary(), sort_keys=True))
    return 0


def _provider_gate_blocked() -> bool:
    provider_gate = build_provider_activation_readiness_final_gate()
    return (
        provider_gate.decision == "blocked"
        and provider_gate.providers_enabled is False
        and provider_gate.network_calls_enabled is False
        and provider_gate.production_provider_allowed is False
    )


def _standard_library_json_get_request_callable(
    base_url: str,
    auth_material: str,
    query: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    target = base_url
    if query:
        separator = "&" if "?" in target else "?"
        target = f"{target}{separator}{urlencode({str(key): str(value) for key, value in query.items()})}"

    request = Request(target, method="GET")
    request.headers["Accept"] = "application/json"
    request.headers["x-apisports-key"] = auth_material
    with urlopen(request, timeout=10) as response:
        payload_bytes = response.read()
    payload = json.loads(payload_bytes.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ApiFootballSmokeDisabledError("first real local smoke response must be a JSON object")
    return payload


def _validated_result(
    result: ApiFootballFirstRealLocalSmokeResult,
    *,
    environ: Mapping[str, str] | None = None,
) -> ApiFootballFirstRealLocalSmokeResult:
    _assert_output_safe(result, environ=environ)
    return result


def _assert_output_safe(
    result: ApiFootballFirstRealLocalSmokeResult,
    *,
    environ: Mapping[str, str] | None = None,
) -> None:
    config = load_api_football_smoke_config(environ)
    serialized_result = json.dumps(result.public_safe_summary(), default=str, sort_keys=True).lower()
    forbidden_fragments = set(FIRST_REAL_LOCAL_SMOKE_FORBIDDEN_OUTPUT_FRAGMENTS)
    forbidden_fragments.update(env_name.lower() for env_name in API_FOOTBALL_SMOKE_ENV_NAMES)
    forbidden_fragments.update(env_name.lower() for env_name in LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES)
    if config.auth_material:
        forbidden_fragments.add(config.auth_material.lower())
    if config.base_url:
        forbidden_fragments.add(config.base_url.lower())

    if any(fragment and fragment in serialized_result for fragment in forbidden_fragments):
        raise ApiFootballSmokeDisabledError("first real local smoke output contains non-public provider material")


if __name__ == "__main__":
    raise SystemExit(main())
