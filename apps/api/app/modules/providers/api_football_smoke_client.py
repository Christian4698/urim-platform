import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, runtime_checkable

from app.modules.providers.activation_readiness_final_gate import build_provider_activation_readiness_final_gate
from app.modules.providers.api_football_transport import stable_raw_hash
from app.schemas.providers import (
    ProviderActivationReadinessFinalGate,
    ProviderApiFootballSmokeClientStatus,
)

API_FOOTBALL_SMOKE_ENV_NAMES: tuple[str, ...] = (
    "URIM_API_FOOTBALL_SMOKE_ENABLED",
    "URIM_API_FOOTBALL_SMOKE_AUTH",
    "URIM_API_FOOTBALL_SMOKE_BASE_URL",
    "URIM_API_FOOTBALL_SMOKE_READ_ONLY",
    "URIM_API_FOOTBALL_SMOKE_NON_PROD",
)
_SMOKE_ENABLED_ENV = API_FOOTBALL_SMOKE_ENV_NAMES[0]
_SMOKE_AUTH_ENV = API_FOOTBALL_SMOKE_ENV_NAMES[1]
_SMOKE_BASE_URL_ENV = API_FOOTBALL_SMOKE_ENV_NAMES[2]
_SMOKE_READ_ONLY_ENV = API_FOOTBALL_SMOKE_ENV_NAMES[3]
_SMOKE_NON_PROD_ENV = API_FOOTBALL_SMOKE_ENV_NAMES[4]
_APP_ENV_NAME = "APP_ENV"

_TRUE_VALUES = frozenset({"1", "true", "yes", "on", "enabled"})
_PRODUCTION_APP_ENVS = frozenset({"prod", "production"})
_SENSITIVE_PUBLIC_FRAGMENTS = (
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


class ApiFootballSmokeDisabledError(RuntimeError):
    """Raised before an env-gated API-Football smoke action can execute."""


@dataclass(frozen=True, repr=False)
class ApiFootballSmokeConfig:
    smoke_mode_enabled: bool
    auth_material_present: bool
    base_url_present: bool
    read_only_confirmed: bool
    non_production_confirmed: bool
    app_env: str
    auth_material: str = field(default="", repr=False, compare=False)
    base_url: str = field(default="", repr=False, compare=False)

    def public_safe_state(self) -> dict[str, bool | str]:
        return {
            "smoke_mode_enabled": self.smoke_mode_enabled,
            "auth_material_present": self.auth_material_present,
            "base_url_present": self.base_url_present,
            "read_only_confirmed": self.read_only_confirmed,
            "non_production_confirmed": self.non_production_confirmed,
            "app_env": self.app_env,
        }


@dataclass(frozen=True)
class ApiFootballSmokeResult:
    status: str
    provider_gate_consulted: bool
    provider_gate_decision: str
    read_only: bool
    payload_hash: str
    payload_top_level_keys: tuple[str, ...]
    db_ingestion_enabled: bool = False
    prediction_creation_enabled: bool = False
    betting_enabled: bool = False
    credentials_exposed: bool = False

    def public_safe_summary(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "provider_gate_consulted": self.provider_gate_consulted,
            "provider_gate_decision": self.provider_gate_decision,
            "read_only": self.read_only,
            "payload_hash": self.payload_hash,
            "payload_top_level_keys": list(self.payload_top_level_keys),
            "db_ingestion_enabled": self.db_ingestion_enabled,
            "prediction_creation_enabled": self.prediction_creation_enabled,
            "betting_enabled": self.betting_enabled,
            "credentials_exposed": self.credentials_exposed,
        }


@runtime_checkable
class ApiFootballSmokeTransportProtocol(Protocol):
    def smoke_request(
        self,
        *,
        base_url: str,
        auth_material: str,
        query: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]: ...


class ApiFootballSmokeHttpTransport:
    """Injectable smoke transport shell; no HTTP client is created by default."""

    network_calls_enabled_by_default = False
    db_ingestion_enabled = False
    prediction_creation_enabled = False
    betting_enabled = False

    def __init__(
        self,
        request_callable: Callable[[str, str, Mapping[str, Any] | None], Mapping[str, Any]] | None = None,
    ) -> None:
        self._request_callable = request_callable

    def smoke_request(
        self,
        *,
        base_url: str,
        auth_material: str,
        query: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        if self._request_callable is None:
            raise ApiFootballSmokeDisabledError("API-Football smoke HTTP transport requires explicit local injection")
        return self._request_callable(base_url, auth_material, query)


class ApiFootballSmokeClient:
    """Internal env-gated API-Football smoke client, disabled by default."""

    enabled_by_default = False
    network_calls_enabled_by_default = False
    db_ingestion_enabled = False
    prediction_creation_enabled = False
    betting_enabled = False

    def __init__(
        self,
        transport: ApiFootballSmokeTransportProtocol | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self._transport = transport
        self._environ = environ

    def run_smoke_check(self, query: Mapping[str, Any] | None = None) -> ApiFootballSmokeResult:
        config = load_api_football_smoke_config(self._environ)
        provider_gate = build_provider_activation_readiness_final_gate()
        self._require_explicit_smoke(config, provider_gate)

        if self._transport is None:
            raise _disabled("transport_explicitly_injected_required")

        raw_payload = dict(
            self._transport.smoke_request(
                base_url=config.base_url,
                auth_material=config.auth_material,
                query=query,
            )
        )
        _assert_no_smoke_material_leaks(raw_payload, config)
        payload_hash = stable_raw_hash({"smoke_payload": raw_payload})
        return ApiFootballSmokeResult(
            status="completed_with_injected_transport_only",
            provider_gate_consulted=True,
            provider_gate_decision=provider_gate.decision,
            read_only=True,
            payload_hash=payload_hash,
            payload_top_level_keys=tuple(sorted(str(key) for key in raw_payload)),
        )

    def _require_explicit_smoke(
        self,
        config: ApiFootballSmokeConfig,
        provider_gate: ProviderActivationReadinessFinalGate,
    ) -> None:
        refusal_reasons: list[str] = []
        if not config.smoke_mode_enabled:
            refusal_reasons.append("smoke_mode_not_explicitly_enabled")
        if not config.auth_material_present:
            refusal_reasons.append("local_auth_material_missing")
        if not config.base_url_present:
            refusal_reasons.append("local_provider_location_missing")
        if not config.read_only_confirmed:
            refusal_reasons.append("read_only_confirmation_missing")
        if not config.non_production_confirmed:
            refusal_reasons.append("non_production_confirmation_missing")
        if config.app_env.strip().lower() in _PRODUCTION_APP_ENVS:
            refusal_reasons.append("production_environment_refused")
        if (
            provider_gate.decision != "blocked"
            or provider_gate.providers_enabled is not False
            or provider_gate.network_calls_enabled is not False
            or provider_gate.production_provider_allowed is not False
        ):
            refusal_reasons.append("provider_activation_gate_not_blocked")

        if refusal_reasons:
            raise _disabled(*refusal_reasons)


def _env_true(value: str | None) -> bool:
    return value is not None and value.strip().lower() in _TRUE_VALUES


def _clean_env_value(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def load_api_football_smoke_config(environ: Mapping[str, str] | None = None) -> ApiFootballSmokeConfig:
    environment = os.environ if environ is None else environ
    auth_material = _clean_env_value(environment.get(_SMOKE_AUTH_ENV))
    base_url = _clean_env_value(environment.get(_SMOKE_BASE_URL_ENV))
    app_env = _clean_env_value(environment.get(_APP_ENV_NAME)) or "development"
    return ApiFootballSmokeConfig(
        smoke_mode_enabled=_env_true(environment.get(_SMOKE_ENABLED_ENV)),
        auth_material_present=bool(auth_material),
        base_url_present=bool(base_url),
        read_only_confirmed=_env_true(environment.get(_SMOKE_READ_ONLY_ENV)),
        non_production_confirmed=_env_true(environment.get(_SMOKE_NON_PROD_ENV)),
        app_env=app_env,
        auth_material=auth_material,
        base_url=base_url,
    )


def build_api_football_smoke_client_status(
    status: ProviderApiFootballSmokeClientStatus | None = None,
    environ: Mapping[str, str] | None = None,
) -> ProviderApiFootballSmokeClientStatus:
    """Return a public-safe smoke status, ignoring environment-derived activation state."""
    _ = (status, load_api_football_smoke_config(environ))
    return ProviderApiFootballSmokeClientStatus()


def _disabled(*reason_codes: str) -> ApiFootballSmokeDisabledError:
    return ApiFootballSmokeDisabledError(
        "API-Football smoke client is disabled: " + ", ".join(sorted(reason_codes))
    )


def _assert_no_smoke_material_leaks(payload: Mapping[str, Any], config: ApiFootballSmokeConfig) -> None:
    serialized_payload = json.dumps(payload, default=str, sort_keys=True).lower()
    forbidden_fragments = set(_SENSITIVE_PUBLIC_FRAGMENTS)
    forbidden_fragments.update(env_name.lower() for env_name in API_FOOTBALL_SMOKE_ENV_NAMES)
    if config.auth_material:
        forbidden_fragments.add(config.auth_material.lower())
    if config.base_url:
        forbidden_fragments.add(config.base_url.lower())

    if any(fragment and fragment in serialized_payload for fragment in forbidden_fragments):
        raise ApiFootballSmokeDisabledError("API-Football smoke payload contains non-public provider material")
