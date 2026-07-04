import json
import os
import subprocess
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.modules.providers.api_football_smoke_client import (
    API_FOOTBALL_SMOKE_ENV_NAMES,
    ApiFootballSmokeDisabledError,
    load_api_football_smoke_config,
)

LOCAL_SECRET_ENV_PREFLIGHT_PROVIDER = "api-football"
LOCAL_SECRET_ENV_PREFLIGHT_MODE = "local_secret_env_preflight_only"
LOCAL_SECRET_ENV_PREFLIGHT_NOT_READY_STATUS = "not_ready_for_manual_smoke_attempt"
LOCAL_SECRET_ENV_PREFLIGHT_READY_STATUS = "ready_for_manual_smoke_attempt"

LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES: tuple[str, ...] = (
    "URIM_LOCAL_PREFLIGHT_NO_DB_WRITE_CONFIRMED",
    "URIM_LOCAL_PREFLIGHT_NO_PREDICTION_CONFIRMED",
    "URIM_LOCAL_PREFLIGHT_NO_BETTING_CONFIRMED",
)

_NO_DB_WRITE_ENV = LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES[0]
_NO_PREDICTION_ENV = LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES[1]
_NO_BETTING_ENV = LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES[2]
_PRODUCTION_APP_ENVS = frozenset({"prod", "production"})
_TRUE_VALUES = frozenset({"1", "true", "yes", "on", "enabled", "confirmed"})
_FORBIDDEN_OUTPUT_FRAGMENTS = (
    "api_key",
    "authorization",
    "bearer",
    "credential",
    "provider_credentials",
    "password",
    "token",
    "http://",
    "https://",
    "api-football.com",
    "api-sports",
    "rapidapi",
    "x-rapidapi",
)
_FORBIDDEN_ROUTE_FRAGMENTS = (
    "/api/v1/providers/smoke",
    "/api/v1/providers/local-smoke",
    "/api/v1/providers/preflight",
    "/api/v1/providers/local-preflight",
    "/api/v1/providers/api-football/preflight",
    "/api/v1/providers/api-football/local-preflight",
)
_PROVIDER_MATERIAL_SUFFIXES = frozenset({".json", ".jsonl", ".ndjson", ".log", ".txt", ".out"})
_PROVIDER_MATERIAL_NAME_MARKERS = (
    "api_football",
    "api-football",
    "provider",
    "payload",
    "response",
    "smoke",
)
_PROVIDER_MATERIAL_CONTENT_MARKERS = (
    "x-rapidapi-key",
    "api-football.com",
    "api-sports",
    "smoke_payload",
    "raw_payload",
)


@dataclass(frozen=True)
class LocalApiFootballPreflightRepoChecks:
    public_smoke_routes_absent: bool = True
    provider_material_absent: bool = True
    git_status_clean_recommended: bool = True


@dataclass(frozen=True)
class LocalApiFootballSecretEnvPreflightResult:
    status: str = LOCAL_SECRET_ENV_PREFLIGHT_NOT_READY_STATUS
    ready_for_manual_smoke_attempt: bool = False
    provider: str = LOCAL_SECRET_ENV_PREFLIGHT_PROVIDER
    mode: str = LOCAL_SECRET_ENV_PREFLIGHT_MODE
    non_production_environment: bool = False
    smoke_mode_enabled: bool = False
    read_only_confirmed: bool = False
    no_db_write_confirmed: bool = False
    no_prediction_confirmed: bool = False
    no_betting_confirmed: bool = False
    secrets_detected_as_present: bool = False
    provider_reference_present: bool = False
    public_smoke_routes_absent: bool = True
    provider_material_absent: bool = True
    git_status_clean_recommended: bool = True
    db_writes: bool = False
    prediction_created: bool = False
    betting_created: bool = False
    blocking_reasons: tuple[str, ...] = ()

    def public_safe_summary(self) -> dict[str, Any]:
        summary = asdict(self)
        summary["blocking_reasons"] = list(self.blocking_reasons)
        return summary


def run_local_api_football_secret_env_preflight(
    *,
    environ: Mapping[str, str] | None = None,
    repo_checks: Mapping[str, bool] | LocalApiFootballPreflightRepoChecks | None = None,
    repo_root: str | Path | None = None,
) -> LocalApiFootballSecretEnvPreflightResult:
    environment = os.environ if environ is None else environ
    config = load_api_football_smoke_config(environment)
    local_repo_checks = _resolve_repo_checks(repo_checks=repo_checks, repo_root=repo_root)

    non_production_environment = config.app_env.strip().lower() not in _PRODUCTION_APP_ENVS
    no_db_write_confirmed = _env_true(environment.get(_NO_DB_WRITE_ENV))
    no_prediction_confirmed = _env_true(environment.get(_NO_PREDICTION_ENV))
    no_betting_confirmed = _env_true(environment.get(_NO_BETTING_ENV))

    blocking_reasons: list[str] = []
    if not non_production_environment:
        blocking_reasons.append("production_environment_refused")
    if not config.smoke_mode_enabled:
        blocking_reasons.append("smoke_mode_not_explicitly_enabled")
    if not config.read_only_confirmed:
        blocking_reasons.append("read_only_confirmation_missing")
    if not no_db_write_confirmed:
        blocking_reasons.append("no_db_write_confirmation_missing")
    if not no_prediction_confirmed:
        blocking_reasons.append("no_prediction_confirmation_missing")
    if not no_betting_confirmed:
        blocking_reasons.append("no_betting_confirmation_missing")
    if not config.auth_material_present:
        blocking_reasons.append("local_auth_material_missing")
    if not config.base_url_present:
        blocking_reasons.append("local_provider_reference_missing")
    if not local_repo_checks.public_smoke_routes_absent:
        blocking_reasons.append("public_smoke_route_present")
    if not local_repo_checks.provider_material_absent:
        blocking_reasons.append("provider_material_present_in_repo")

    ready = not blocking_reasons
    result = LocalApiFootballSecretEnvPreflightResult(
        status=LOCAL_SECRET_ENV_PREFLIGHT_READY_STATUS if ready else LOCAL_SECRET_ENV_PREFLIGHT_NOT_READY_STATUS,
        ready_for_manual_smoke_attempt=ready,
        non_production_environment=non_production_environment,
        smoke_mode_enabled=config.smoke_mode_enabled,
        read_only_confirmed=config.read_only_confirmed,
        no_db_write_confirmed=no_db_write_confirmed,
        no_prediction_confirmed=no_prediction_confirmed,
        no_betting_confirmed=no_betting_confirmed,
        secrets_detected_as_present=config.auth_material_present,
        provider_reference_present=config.base_url_present,
        public_smoke_routes_absent=local_repo_checks.public_smoke_routes_absent,
        provider_material_absent=local_repo_checks.provider_material_absent,
        git_status_clean_recommended=local_repo_checks.git_status_clean_recommended,
        blocking_reasons=tuple(blocking_reasons),
    )
    _assert_local_secret_env_preflight_output_safe(result, environ=environment)
    return result


def assert_local_secret_env_preflight_output_safe(
    result: LocalApiFootballSecretEnvPreflightResult,
    *,
    environ: Mapping[str, str] | None = None,
) -> None:
    _assert_local_secret_env_preflight_output_safe(result, environ=environ)


def main() -> int:
    result = run_local_api_football_secret_env_preflight(environ=os.environ)
    print(json.dumps(result.public_safe_summary(), sort_keys=True))
    return 0


def _assert_local_secret_env_preflight_output_safe(
    result: LocalApiFootballSecretEnvPreflightResult,
    *,
    environ: Mapping[str, str] | None = None,
) -> None:
    config = load_api_football_smoke_config(environ)
    serialized_result = json.dumps(result.public_safe_summary(), default=str, sort_keys=True).lower()
    forbidden_fragments = set(_FORBIDDEN_OUTPUT_FRAGMENTS)
    forbidden_fragments.update(env_name.lower() for env_name in API_FOOTBALL_SMOKE_ENV_NAMES)
    forbidden_fragments.update(env_name.lower() for env_name in LOCAL_SECRET_ENV_PREFLIGHT_CONFIRMATION_ENV_NAMES)
    if config.auth_material:
        forbidden_fragments.add(config.auth_material.lower())
    if config.base_url:
        forbidden_fragments.add(config.base_url.lower())

    if any(fragment and fragment in serialized_result for fragment in forbidden_fragments):
        raise ApiFootballSmokeDisabledError("local API-Football preflight output contains non-public material")


def _resolve_repo_checks(
    *,
    repo_checks: Mapping[str, bool] | LocalApiFootballPreflightRepoChecks | None,
    repo_root: str | Path | None,
) -> LocalApiFootballPreflightRepoChecks:
    if isinstance(repo_checks, LocalApiFootballPreflightRepoChecks):
        return repo_checks
    if repo_checks is not None:
        return LocalApiFootballPreflightRepoChecks(
            public_smoke_routes_absent=bool(repo_checks.get("public_smoke_routes_absent", True)),
            provider_material_absent=bool(repo_checks.get("provider_material_absent", True)),
            git_status_clean_recommended=bool(repo_checks.get("git_status_clean_recommended", True)),
        )

    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    return LocalApiFootballPreflightRepoChecks(
        public_smoke_routes_absent=_public_smoke_routes_absent(root),
        provider_material_absent=_provider_material_absent(root),
        git_status_clean_recommended=_git_status_clean(root),
    )


def _public_smoke_routes_absent(repo_root: Path) -> bool:
    api_paths = [repo_root / "apps" / "api" / "app" / "main.py", *(repo_root / "apps" / "api" / "app" / "api").rglob("*.py")]
    for source_path in api_paths:
        if not source_path.is_file():
            continue
        source = source_path.read_text(encoding="utf-8", errors="ignore").lower()
        if any(fragment in source for fragment in _FORBIDDEN_ROUTE_FRAGMENTS):
            return False
    return True


def _provider_material_absent(repo_root: Path) -> bool:
    for source_path in _changed_or_untracked_paths(repo_root):
        if not source_path.is_file() or source_path.suffix.lower() not in _PROVIDER_MATERIAL_SUFFIXES:
            continue
        lowered_name = source_path.name.lower()
        if not any(marker in lowered_name for marker in _PROVIDER_MATERIAL_NAME_MARKERS):
            continue
        source = source_path.read_text(encoding="utf-8", errors="ignore").lower()
        if any(marker in source for marker in _PROVIDER_MATERIAL_CONTENT_MARKERS):
            return False
    return True


def _changed_or_untracked_paths(repo_root: Path) -> list[Path]:
    try:
        completed = subprocess.run(
            ["git", "status", "--short", "--untracked-files=all"],
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if completed.returncode != 0:
        return []

    paths: list[Path] = []
    for line in completed.stdout.splitlines():
        candidate = line[3:].strip()
        if " -> " in candidate:
            candidate = candidate.rsplit(" -> ", maxsplit=1)[-1].strip()
        if candidate:
            paths.append(repo_root / candidate)
    return paths


def _git_status_clean(repo_root: Path) -> bool:
    try:
        completed = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0 and not completed.stdout.strip()


def _env_true(value: str | None) -> bool:
    return value is not None and value.strip().lower() in _TRUE_VALUES


if __name__ == "__main__":
    raise SystemExit(main())
