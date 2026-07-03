import json
import os
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from typing import Any

from app.modules.providers.api_football_smoke_client import (
    API_FOOTBALL_SMOKE_ENV_NAMES,
    ApiFootballSmokeDisabledError,
    load_api_football_smoke_config,
)
from app.modules.providers.api_football_smoke_runner import (
    MANUAL_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS,
    run_manual_api_football_smoke_check,
)

LOCAL_HTTP_SMOKE_PROVIDER = "api-football"
LOCAL_HTTP_SMOKE_MODE = "local_http_smoke_only"
LOCAL_HTTP_SMOKE_DISABLED_STATUS = "disabled_until_explicit_local_http_smoke"
LOCAL_HTTP_SMOKE_COMPLETED_STATUS = "completed_with_injected_request_callable_only"
LOCAL_HTTP_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS = "refused_unsafe_local_http_smoke_output"
LOCAL_HTTP_SMOKE_FORBIDDEN_OUTPUT_FRAGMENTS = (
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
)

RequestCallable = Callable[[str, str, Mapping[str, Any] | None], Mapping[str, Any]]


@dataclass(frozen=True)
class LocalApiFootballHttpSmokeHarnessResult:
    status: str = LOCAL_HTTP_SMOKE_DISABLED_STATUS
    executed: bool = False
    provider: str = LOCAL_HTTP_SMOKE_PROVIDER
    mode: str = LOCAL_HTTP_SMOKE_MODE
    db_writes: bool = False
    prediction_created: bool = False
    betting_created: bool = False
    payload_hash: str | None = None

    def public_safe_summary(self) -> dict[str, Any]:
        return asdict(self)


class _InjectedRequestCallableTransport:
    def __init__(self, request_callable: RequestCallable) -> None:
        self._request_callable = request_callable

    def smoke_request(
        self,
        *,
        base_url: str,
        auth_material: str,
        query: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        return self._request_callable(base_url, auth_material, query)


def run_local_api_football_http_smoke_harness(
    *,
    request_callable: RequestCallable | None = None,
    environ: Mapping[str, str] | None = None,
    query: Mapping[str, Any] | None = None,
) -> LocalApiFootballHttpSmokeHarnessResult:
    """Run the local-only harness only through an explicitly injected request callable."""
    if request_callable is None:
        return _validated_harness_result(
            LocalApiFootballHttpSmokeHarnessResult(),
            environ=environ,
        )

    manual_result = run_manual_api_football_smoke_check(
        transport=_InjectedRequestCallableTransport(request_callable),
        environ=environ,
        query=query,
    )
    if manual_result.executed:
        status = LOCAL_HTTP_SMOKE_COMPLETED_STATUS
    elif manual_result.status == MANUAL_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS:
        status = LOCAL_HTTP_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS
    else:
        status = LOCAL_HTTP_SMOKE_DISABLED_STATUS

    return _validated_harness_result(
        LocalApiFootballHttpSmokeHarnessResult(
            status=status,
            executed=manual_result.executed,
            payload_hash=manual_result.payload_hash,
        ),
        environ=environ,
    )


def assert_local_api_football_http_smoke_harness_output_safe(
    result: LocalApiFootballHttpSmokeHarnessResult,
    *,
    environ: Mapping[str, str] | None = None,
) -> None:
    config = load_api_football_smoke_config(environ)
    serialized_result = json.dumps(result.public_safe_summary(), default=str, sort_keys=True).lower()
    forbidden_fragments = set(LOCAL_HTTP_SMOKE_FORBIDDEN_OUTPUT_FRAGMENTS)
    forbidden_fragments.update(env_name.lower() for env_name in API_FOOTBALL_SMOKE_ENV_NAMES)
    if config.auth_material:
        forbidden_fragments.add(config.auth_material.lower())
    if config.base_url:
        forbidden_fragments.add(config.base_url.lower())

    if any(fragment and fragment in serialized_result for fragment in forbidden_fragments):
        raise ApiFootballSmokeDisabledError(
            "local API-Football HTTP smoke harness output contains non-public provider material"
        )


def main() -> int:
    result = run_local_api_football_http_smoke_harness(environ=os.environ)
    print(json.dumps(result.public_safe_summary(), sort_keys=True))
    return 0


def _validated_harness_result(
    result: LocalApiFootballHttpSmokeHarnessResult,
    *,
    environ: Mapping[str, str] | None = None,
) -> LocalApiFootballHttpSmokeHarnessResult:
    assert_local_api_football_http_smoke_harness_output_safe(result, environ=environ)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
