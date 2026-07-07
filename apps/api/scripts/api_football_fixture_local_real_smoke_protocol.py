from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import date as calendar_date
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Final


_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.modules.providers.api_football_fixture_request_builder import (  # noqa: E402
    ApiFootballFixtureRequestValidationError,
    build_api_football_fixture_read_only_request,
)


def _literal(*parts: str) -> str:
    return "".join(parts)


FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_PROVIDER: Final = "api-football"
FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENDPOINT: Final = "/fixtures"
FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_MODE: Final = "fixture_local_real_smoke_protocol_only"

FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES: Final = (
    "APP_ENV",
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_ENABLED",
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_DATE",
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_TIMEZONE",
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_READ_ONLY",
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_NON_PROD",
    "URIM_LOCAL_PREFLIGHT_NO_DB_WRITE_CONFIRMED",
    "URIM_LOCAL_PREFLIGHT_NO_PREDICTION_CONFIRMED",
    "URIM_LOCAL_PREFLIGHT_NO_BETTING_CONFIRMED",
)

_APP_ENV = FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES[0]
_SMOKE_ENABLED_ENV = FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES[1]
_SMOKE_DATE_ENV = FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES[2]
_SMOKE_TIMEZONE_ENV = FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES[3]
_SMOKE_READ_ONLY_ENV = FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES[4]
_SMOKE_NON_PROD_ENV = FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES[5]
_NO_DB_WRITE_ENV = FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES[6]
_NO_PREDICTION_ENV = FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES[7]
_NO_BETTING_ENV = FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES[8]

_PRODUCTION_APP_ENVS: Final = frozenset({"prod", "production"})
_TRUE_VALUES: Final = frozenset({"1", "true", "yes", "on", "enabled", "confirmed"})
_DATE_PATTERN: Final = re.compile(r"\d{4}-\d{2}-\d{2}")

_UNSUPPORTED_FIXTURE_QUERY_ENVS: Final = (
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_LEAGUE",
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_TEAM",
    "URIM_API_FOOTBALL_FIXTURE_SMOKE_SEASON",
)
_FORBIDDEN_FIXTURE_SMOKE_ENV_MARKERS: Final = (
    "ODDS",
    "BOOKMAKER",
    "STAKE",
    "PREDICTION",
    "PREDICTIONS",
    "BET",
    "BETTING",
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
)


class ApiFootballFixtureLocalRealSmokeProtocolError(RuntimeError):
    """Raised when a Phase 30 protocol result would not be public-safe."""


@dataclass(frozen=True)
class ApiFootballFixtureLocalRealSmokeProtocolResult:
    provider: str = FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_PROVIDER
    endpoint: str = FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENDPOINT
    mode: str = FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_MODE
    executed: bool = False
    ready_for_fixture_real_smoke: bool = False
    approved_query: Mapping[str, str] | None = None
    db_writes: bool = False
    prediction_created: bool = False
    betting_created: bool = False
    blocking_reasons: tuple[str, ...] = ()

    def public_safe_summary(self) -> dict[str, Any]:
        summary = asdict(self)
        if self.approved_query is None:
            summary.pop("approved_query")
        else:
            summary["approved_query"] = dict(self.approved_query)
        if self.blocking_reasons:
            summary["blocking_reasons"] = list(self.blocking_reasons)
        else:
            summary.pop("blocking_reasons")
        return summary


def run_api_football_fixture_local_real_smoke_protocol(
    *,
    environ: Mapping[str, str] | None = None,
) -> ApiFootballFixtureLocalRealSmokeProtocolResult:
    environment = os.environ if environ is None else environ
    blocking_reasons: list[str] = []

    app_env = environment.get(_APP_ENV, "").strip().lower()
    if app_env in _PRODUCTION_APP_ENVS:
        blocking_reasons.append("production_environment_refused")
    elif app_env != "development":
        blocking_reasons.append("development_environment_missing")

    if not _env_true(environment.get(_SMOKE_ENABLED_ENV)):
        blocking_reasons.append("fixture_smoke_not_explicitly_enabled")
    if not _env_true(environment.get(_SMOKE_READ_ONLY_ENV)):
        blocking_reasons.append("read_only_confirmation_missing")
    if not _env_true(environment.get(_SMOKE_NON_PROD_ENV)):
        blocking_reasons.append("non_production_confirmation_missing")
    if not _env_true(environment.get(_NO_DB_WRITE_ENV)):
        blocking_reasons.append("no_db_write_confirmation_missing")
    if not _env_true(environment.get(_NO_PREDICTION_ENV)):
        blocking_reasons.append("no_prediction_confirmation_missing")
    if not _env_true(environment.get(_NO_BETTING_ENV)):
        blocking_reasons.append("no_betting_confirmation_missing")

    date_value = environment.get(_SMOKE_DATE_ENV, "")
    timezone_value = environment.get(_SMOKE_TIMEZONE_ENV, "")
    if not date_value:
        blocking_reasons.append("fixture_smoke_date_missing")
    elif not _valid_fixture_smoke_date(date_value):
        blocking_reasons.append("fixture_smoke_date_invalid")
    if not timezone_value.strip():
        blocking_reasons.append("fixture_smoke_timezone_missing")

    _append_unsupported_query_reasons(environment, blocking_reasons)
    approved_query = _approved_query_or_none(
        date_value=date_value,
        timezone_value=timezone_value,
        blocking_reasons=blocking_reasons,
    )
    ready = not blocking_reasons
    result = ApiFootballFixtureLocalRealSmokeProtocolResult(
        ready_for_fixture_real_smoke=ready,
        approved_query=approved_query if ready else None,
        blocking_reasons=tuple(blocking_reasons),
    )
    assert_api_football_fixture_local_real_smoke_protocol_output_safe(result)
    return result


def assert_api_football_fixture_local_real_smoke_protocol_output_safe(
    result: ApiFootballFixtureLocalRealSmokeProtocolResult,
) -> None:
    serialized_result = json.dumps(
        result.public_safe_summary(),
        default=str,
        sort_keys=True,
    ).lower()
    forbidden_fragments = set(_FORBIDDEN_OUTPUT_FRAGMENTS)
    forbidden_fragments.update(env_name.lower() for env_name in FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES)
    if any(fragment and fragment in serialized_result for fragment in forbidden_fragments):
        raise ApiFootballFixtureLocalRealSmokeProtocolError(
            "fixture local real smoke protocol output contains non-public material"
        )


def main() -> int:
    result = run_api_football_fixture_local_real_smoke_protocol(environ=os.environ)
    print(json.dumps(result.public_safe_summary(), sort_keys=True))
    return 0


def _approved_query_or_none(
    *,
    date_value: str,
    timezone_value: str,
    blocking_reasons: list[str],
) -> dict[str, str] | None:
    if blocking_reasons:
        return None
    try:
        request = build_api_football_fixture_read_only_request(
            {"date": date_value.strip(), "timezone": timezone_value.strip()}
        )
    except ApiFootballFixtureRequestValidationError:
        blocking_reasons.append("approved_query_validation_failed")
        return None
    return {key: str(value) for key, value in request.query.items()}


def _append_unsupported_query_reasons(
    environment: Mapping[str, str],
    blocking_reasons: list[str],
) -> None:
    if any(environment.get(env_name, "").strip() for env_name in _UNSUPPORTED_FIXTURE_QUERY_ENVS):
        _append_once(blocking_reasons, "unsupported_fixture_query_parameter_present")

    for env_name, env_value in environment.items():
        upper_env_name = env_name.upper()
        if not upper_env_name.startswith("URIM_API_FOOTBALL_FIXTURE_SMOKE_"):
            continue
        if not str(env_value).strip():
            continue
        if any(marker in upper_env_name for marker in _FORBIDDEN_FIXTURE_SMOKE_ENV_MARKERS):
            _append_once(blocking_reasons, "forbidden_fixture_smoke_parameter_present")


def _valid_fixture_smoke_date(value: str) -> bool:
    candidate = value.strip()
    if not _DATE_PATTERN.fullmatch(candidate):
        return False
    try:
        calendar_date.fromisoformat(candidate)
    except ValueError:
        return False
    return True


def _env_true(value: str | None) -> bool:
    return value is not None and value.strip().lower() in _TRUE_VALUES


def _append_once(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


if __name__ == "__main__":
    raise SystemExit(main())
