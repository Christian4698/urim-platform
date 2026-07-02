import json
import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from app.modules.providers.api_football_smoke_client import (
    API_FOOTBALL_SMOKE_ENV_NAMES,
    ApiFootballSmokeClient,
    ApiFootballSmokeDisabledError,
    ApiFootballSmokeTransportProtocol,
    load_api_football_smoke_config,
)

MANUAL_SMOKE_PROVIDER = "api-football"
MANUAL_SMOKE_MODE = "manual_smoke_only"
MANUAL_SMOKE_DISABLED_STATUS = "disabled_until_explicit_local_manual_smoke"
MANUAL_SMOKE_COMPLETED_STATUS = "completed_with_injected_transport_only"
MANUAL_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS = "refused_unsafe_manual_smoke_output"
MANUAL_SMOKE_FORBIDDEN_OUTPUT_FRAGMENTS = (
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


@dataclass(frozen=True)
class ManualApiFootballSmokeRunResult:
    status: str = MANUAL_SMOKE_DISABLED_STATUS
    executed: bool = False
    provider: str = MANUAL_SMOKE_PROVIDER
    mode: str = MANUAL_SMOKE_MODE
    db_writes: bool = False
    prediction_created: bool = False
    betting_created: bool = False
    payload_hash: str | None = None

    def public_safe_summary(self) -> dict[str, Any]:
        return asdict(self)


def run_manual_api_football_smoke_check(
    *,
    transport: ApiFootballSmokeTransportProtocol | None = None,
    environ: Mapping[str, str] | None = None,
    query: Mapping[str, Any] | None = None,
) -> ManualApiFootballSmokeRunResult:
    """Run the API-Football smoke client only through an explicitly injected local transport."""
    client = ApiFootballSmokeClient(transport=transport, environ=environ)
    try:
        smoke_result = client.run_smoke_check(query=query)
    except ApiFootballSmokeDisabledError as exc:
        status = (
            MANUAL_SMOKE_REFUSED_UNSAFE_OUTPUT_STATUS
            if "non-public provider material" in str(exc)
            else MANUAL_SMOKE_DISABLED_STATUS
        )
        return _validated_manual_result(
            ManualApiFootballSmokeRunResult(status=status),
            environ=environ,
        )

    result = ManualApiFootballSmokeRunResult(
        status=MANUAL_SMOKE_COMPLETED_STATUS,
        executed=True,
        payload_hash=smoke_result.payload_hash,
    )
    return _validated_manual_result(result, environ=environ)


def assert_manual_api_football_smoke_output_safe(
    result: ManualApiFootballSmokeRunResult,
    *,
    environ: Mapping[str, str] | None = None,
) -> None:
    config = load_api_football_smoke_config(environ)
    serialized_result = json.dumps(result.public_safe_summary(), default=str, sort_keys=True).lower()
    forbidden_fragments = set(MANUAL_SMOKE_FORBIDDEN_OUTPUT_FRAGMENTS)
    forbidden_fragments.update(env_name.lower() for env_name in API_FOOTBALL_SMOKE_ENV_NAMES)
    if config.auth_material:
        forbidden_fragments.add(config.auth_material.lower())
    if config.base_url:
        forbidden_fragments.add(config.base_url.lower())

    if any(fragment and fragment in serialized_result for fragment in forbidden_fragments):
        raise ApiFootballSmokeDisabledError("manual API-Football smoke output contains non-public provider material")


def main() -> int:
    result = run_manual_api_football_smoke_check(environ=os.environ)
    print(json.dumps(result.public_safe_summary(), sort_keys=True))
    return 0


def _validated_manual_result(
    result: ManualApiFootballSmokeRunResult,
    *,
    environ: Mapping[str, str] | None = None,
) -> ManualApiFootballSmokeRunResult:
    assert_manual_api_football_smoke_output_safe(result, environ=environ)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
