from __future__ import annotations

import argparse
import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
import json
import sys
import time
from typing import Any, Final, Protocol
from uuid import uuid4

from redis import Redis
from sqlalchemy.exc import SQLAlchemyError

from app.cli import kairos_journal, sports_sync
from app.core.business_time import utc_now
from app.core.config import settings
from app.modules.sports_data.provider import (
    ApiFootballDisabledError,
    ApiFootballRequestError,
)
from app.modules.sports_data.discovery import RETENTION_FUNNEL_FIELDS
from app.modules.sports_data.sync import SportsSyncConfigurationError


LOCK_KEY: Final = "urim:kairos:daily-operations:v1:lock"
STATUS_KEY: Final = "urim:kairos:daily-operations:v1:status"
LOCK_TTL_SECONDS: Final = 30 * 60
STATUS_TTL_SECONDS: Final = 7 * 24 * 60 * 60
REDIS_TIMEOUT_SECONDS: Final = 1.0
STEP_TIMEOUTS: Final = {
    "daily_discovery": 300.0,
    "daily_refresh": 300.0,
    "snapshot": 120.0,
    "resolve": 120.0,
    "report": 60.0,
}
_RELEASE_LOCK_SCRIPT: Final = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
""".strip()


class DailyOperationsUnavailable(RuntimeError):
    """Raised when the orchestrator cannot make a safe decision."""


class DailyOperationsRetentionFunnelError(DailyOperationsUnavailable):
    """Raised when retention metrics are missing or contradictory."""


class RedisOperationsClient(Protocol):
    def set(
        self,
        name: str,
        value: str,
        *,
        nx: bool = False,
        ex: int | None = None,
    ) -> object: ...

    def get(self, name: str) -> object: ...

    def eval(
        self,
        script: str,
        numkeys: int,
        *keys_and_args: object,
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class OperationStep:
    name: str
    critical: bool
    timeout_seconds: float
    runner: Callable[[date], Awaitable[Mapping[str, Any]]]


@dataclass(slots=True)
class OperationMetrics:
    synchronization_succeeded: int = 0
    synchronization_failed: int = 0
    fixtures_received: int = 0
    fixtures_retained: int = 0
    matches_evaluated: int = 0
    snapshots_created: int = 0
    resolutions_created: int = 0
    opportunities_generated: int = 0
    no_bet_count: int = 0
    insufficient_data_count: int = 0
    provider_error_count: int = 0
    redis_fail_closed_count: int = 0
    postgresql_error_count: int = 0
    quota_remaining_daily: int | None = None
    quota_remaining_minute: int | None = None
    retention_funnel: dict[str, int] = field(
        default_factory=lambda: {
            field_name: 0 for field_name in RETENTION_FUNNEL_FIELDS
        }
    )
    step_duration_ms: dict[str, int] = field(default_factory=dict)


class RedisDailyOperationsGuard:
    def __init__(
        self,
        *,
        redis_url: str | None = None,
        client: RedisOperationsClient | None = None,
    ) -> None:
        self._client = client
        self._redis_url = redis_url

    def acquire(self, token: str) -> bool:
        try:
            result = self._get_client().set(
                LOCK_KEY,
                token,
                nx=True,
                ex=LOCK_TTL_SECONDS,
            )
        except Exception as exc:
            raise DailyOperationsUnavailable(
                "daily_operations_redis_unavailable"
            ) from exc
        return bool(result)

    def release(self, token: str) -> bool:
        try:
            result = self._get_client().eval(
                _RELEASE_LOCK_SCRIPT,
                1,
                LOCK_KEY,
                token,
            )
        except Exception as exc:
            raise DailyOperationsUnavailable(
                "daily_operations_redis_release_unavailable"
            ) from exc
        return int(result) == 1

    def save_status(self, summary: Mapping[str, Any]) -> None:
        encoded = json.dumps(
            summary,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        try:
            stored = self._get_client().set(
                STATUS_KEY,
                encoded,
                ex=STATUS_TTL_SECONDS,
            )
        except Exception as exc:
            raise DailyOperationsUnavailable(
                "daily_operations_status_unavailable"
            ) from exc
        if not stored:
            raise DailyOperationsUnavailable(
                "daily_operations_status_unavailable"
            )

    def read_status(self) -> dict[str, Any] | None:
        try:
            raw = self._get_client().get(STATUS_KEY)
        except Exception as exc:
            raise DailyOperationsUnavailable(
                "daily_operations_status_unavailable"
            ) from exc
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        if not isinstance(raw, str) or len(raw) > 50_000:
            raise DailyOperationsUnavailable(
                "daily_operations_status_invalid"
            )
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DailyOperationsUnavailable(
                "daily_operations_status_invalid"
            ) from exc
        if not isinstance(value, dict):
            raise DailyOperationsUnavailable(
                "daily_operations_status_invalid"
            )
        return _sanitize_saved_status(value)

    def _get_client(self) -> RedisOperationsClient:
        if self._client is not None:
            return self._client
        if not self._redis_url:
            raise DailyOperationsUnavailable(
                "daily_operations_redis_not_configured"
            )
        self._client = Redis.from_url(
            self._redis_url,
            socket_connect_timeout=REDIS_TIMEOUT_SECONDS,
            socket_timeout=REDIS_TIMEOUT_SECONDS,
            retry_on_timeout=False,
            health_check_interval=30,
            decode_responses=False,
        )
        return self._client


class DailyOperationsOrchestrator:
    def __init__(
        self,
        *,
        guard: RedisDailyOperationsGuard,
        steps: Sequence[OperationStep] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        emit: Callable[[Mapping[str, Any]], None] | None = None,
    ) -> None:
        self.guard = guard
        self.steps = tuple(_default_steps() if steps is None else steps)
        self.monotonic = monotonic
        self.emit = emit or _emit_json

    async def run(self, target_date: date) -> dict[str, Any]:
        correlation_id = str(uuid4())
        lock_token = uuid4().hex
        started_at = utc_now()
        metrics = OperationMetrics()
        step_results: list[dict[str, Any]] = []
        if not self.guard.acquire(lock_token):
            metrics.redis_fail_closed_count = 1
            summary = _summary(
                correlation_id=correlation_id,
                target_date=target_date,
                started_at=started_at,
                status="failed",
                error_code="daily_operations_already_running",
                step_results=step_results,
                metrics=metrics,
            )
            self.emit(_event(summary, "lock_refused"))
            return summary

        self.emit(
            {
                "event": "daily_operations_started",
                "correlation_id": correlation_id,
                "target_date": target_date.isoformat(),
            }
        )
        final_status = "completed"
        final_error_code: str | None = None
        try:
            for step in self.steps:
                step_started = self.monotonic()
                self.emit(
                    {
                        "event": "daily_operations_step_started",
                        "correlation_id": correlation_id,
                        "step": step.name,
                        "critical": step.critical,
                    }
                )
                try:
                    result = await asyncio.wait_for(
                        step.runner(target_date),
                        timeout=step.timeout_seconds,
                    )
                    safe_metrics = _safe_step_metrics(step.name, result)
                except Exception as exc:
                    duration_ms = max(
                        0,
                        round((self.monotonic() - step_started) * 1_000),
                    )
                    metrics.step_duration_ms[step.name] = duration_ms
                    error_code = _public_step_error(step.name, exc)
                    _record_failure(metrics, step.name, error_code)
                    step_result = {
                        "step": step.name,
                        "status": "failed",
                        "critical": step.critical,
                        "error_code": error_code,
                        "duration_ms": duration_ms,
                    }
                    step_results.append(step_result)
                    self.emit(
                        {
                            "event": "daily_operations_step_failed",
                            "correlation_id": correlation_id,
                            **step_result,
                        }
                    )
                    if step.critical:
                        final_status = "failed"
                        final_error_code = error_code
                        break
                    final_status = "degraded"
                    continue

                duration_ms = max(
                    0,
                    round((self.monotonic() - step_started) * 1_000),
                )
                metrics.step_duration_ms[step.name] = duration_ms
                _record_success(metrics, step.name, safe_metrics)
                step_result = {
                    "step": step.name,
                    "status": "completed",
                    "critical": step.critical,
                    "duration_ms": duration_ms,
                    "metrics": safe_metrics,
                }
                step_results.append(step_result)
                self.emit(
                    {
                        "event": "daily_operations_step_completed",
                        "correlation_id": correlation_id,
                        **step_result,
                    }
                )

            summary = _summary(
                correlation_id=correlation_id,
                target_date=target_date,
                started_at=started_at,
                status=final_status,
                error_code=final_error_code,
                step_results=step_results,
                metrics=metrics,
            )
            self.guard.save_status(summary)
            return summary
        except DailyOperationsUnavailable:
            metrics.redis_fail_closed_count += 1
            return _summary(
                correlation_id=correlation_id,
                target_date=target_date,
                started_at=started_at,
                status="failed",
                error_code="daily_operations_redis_fail_closed",
                step_results=step_results,
                metrics=metrics,
            )
        finally:
            try:
                released = self.guard.release(lock_token)
                if not released:
                    self.emit(
                        {
                            "event": "daily_operations_lock_release_refused",
                            "correlation_id": correlation_id,
                        }
                    )
            except DailyOperationsUnavailable:
                self.emit(
                    {
                        "event": "daily_operations_lock_release_failed",
                        "correlation_id": correlation_id,
                    }
                )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="urim-daily-operations",
        description=(
            "Routine Kairos quotidienne idempotente, verrouillée et sans "
            "bookmaker, cote, mise ni pari."
        ),
    )
    parser.add_argument(
        "command",
        choices=("run", "status"),
        nargs="?",
        default="run",
    )
    parser.add_argument("--date", type=_parse_date)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    guard = RedisDailyOperationsGuard(redis_url=settings.redis_url)
    if args.command == "status":
        if args.date is not None:
            _emit_public_error("daily_operations_status_date_forbidden")
            return 2
        try:
            status = guard.read_status()
        except DailyOperationsUnavailable:
            _emit_public_error("daily_operations_status_unavailable")
            return 3
        _emit_json(
            status
            or {
                "status": "never_run",
                "bookmaker_calls": False,
                "betting_actions": False,
            }
        )
        return 0
    if args.date is None:
        _emit_public_error("daily_operations_date_required")
        return 2
    try:
        summary = asyncio.run(
            DailyOperationsOrchestrator(guard=guard).run(args.date)
        )
    except DailyOperationsUnavailable:
        _emit_public_error("daily_operations_redis_fail_closed")
        return 3
    _emit_json(summary)
    return 0 if summary["status"] in {"completed", "degraded"} else 4


def _default_steps() -> tuple[OperationStep, ...]:
    return (
        OperationStep(
            "daily_discovery",
            True,
            STEP_TIMEOUTS["daily_discovery"],
            _run_daily_discovery,
        ),
        OperationStep(
            "daily_refresh",
            False,
            STEP_TIMEOUTS["daily_refresh"],
            _run_daily_refresh,
        ),
        OperationStep(
            "snapshot",
            True,
            STEP_TIMEOUTS["snapshot"],
            _run_snapshot,
        ),
        OperationStep(
            "resolve",
            False,
            STEP_TIMEOUTS["resolve"],
            _run_resolve,
        ),
        OperationStep(
            "report",
            False,
            STEP_TIMEOUTS["report"],
            _run_report,
        ),
    )


async def _run_daily_discovery(target_date: date) -> Mapping[str, Any]:
    summary = await sports_sync.run_command(
        argparse.Namespace(command="daily-discovery", date=target_date)
    )
    return asdict(summary)


async def _run_daily_refresh(target_date: date) -> Mapping[str, Any]:
    del target_date
    summary = await sports_sync.run_command(
        argparse.Namespace(command="daily-refresh", days=7)
    )
    return asdict(summary)


async def _run_snapshot(target_date: date) -> Mapping[str, Any]:
    return await asyncio.to_thread(
        kairos_journal.run_command,
        argparse.Namespace(command="snapshot", date=target_date),
    )


async def _run_resolve(target_date: date) -> Mapping[str, Any]:
    return await asyncio.to_thread(
        kairos_journal.run_command,
        argparse.Namespace(command="resolve", date=target_date),
    )


async def _run_report(target_date: date) -> Mapping[str, Any]:
    del target_date
    return await asyncio.to_thread(
        kairos_journal.run_command,
        argparse.Namespace(command="report"),
    )


def _safe_step_metrics(
    step: str,
    result: Mapping[str, Any],
) -> dict[str, Any]:
    if step in {"daily_discovery", "daily_refresh"}:
        allowed = (
            "status",
            "request_count",
            "fixtures_received",
            "fixtures_retained",
            "fixtures_ignored",
            "target_matches_added",
            "match_duplicates",
            "quota_remaining_daily",
            "quota_remaining_minute",
            "public_error_code",
        )
    elif step == "snapshot":
        allowed = (
            "matches_evaluated",
            "matches_blocked",
            "opportunities_generated",
            "no_bet_count",
            "insufficient_data_count",
            "stale_data_count",
            "snapshots_created",
            "received",
            "inserted",
            "duplicate",
        )
    elif step == "resolve":
        allowed = ("received", "inserted", "duplicate")
    else:
        performance = result.get("performance")
        if not isinstance(performance, Mapping):
            return {
                "resolved_sample_size": 0,
                "sample_status": "no_sample",
            }
        return {
            key: performance.get(key)
            for key in (
                "total_snapshots",
                "resolved",
                "unresolved",
                "void",
                "resolved_sample_size",
                "sample_status",
            )
        }
    safe_metrics = {
        key: result.get(key)
        for key in allowed
        if key in result
    }
    if step in {"daily_discovery", "daily_refresh"}:
        fixtures_received = _strict_nonnegative_int(
            result.get("fixtures_received")
        )
        fixtures_retained = _strict_nonnegative_int(
            result.get("fixtures_retained")
        )
        retention_funnel = _safe_retention_funnel(
            result.get("retention_funnel")
        )
        if (
            fixtures_received is None
            or fixtures_retained is None
            or fixtures_retained > fixtures_received
            or retention_funnel is None
            or retention_funnel["fixtures_received"]
            != fixtures_received
            or retention_funnel["retained"] != fixtures_retained
        ):
            raise DailyOperationsRetentionFunnelError(
                "daily_operations_retention_funnel_invalid"
            )
        fixtures_ignored = result.get("fixtures_ignored")
        if fixtures_ignored is not None and (
            _strict_nonnegative_int(fixtures_ignored)
            != fixtures_received - fixtures_retained
        ):
            raise DailyOperationsRetentionFunnelError(
                "daily_operations_retention_funnel_invalid"
            )
        safe_metrics["fixtures_received"] = fixtures_received
        safe_metrics["fixtures_retained"] = fixtures_retained
        safe_metrics["retention_funnel"] = retention_funnel
    return safe_metrics


def _record_success(
    metrics: OperationMetrics,
    step: str,
    values: Mapping[str, Any],
) -> None:
    if step in {"daily_discovery", "daily_refresh"}:
        metrics.synchronization_succeeded += 1
        metrics.fixtures_received += _safe_int(
            values.get("fixtures_received")
        )
        metrics.fixtures_retained += _safe_int(
            values.get("fixtures_retained")
        )
        metrics.quota_remaining_daily = _safe_optional_int(
            values.get("quota_remaining_daily")
        )
        metrics.quota_remaining_minute = _safe_optional_int(
            values.get("quota_remaining_minute")
        )
        retention_funnel = _safe_retention_funnel(
            values.get("retention_funnel")
        )
        if retention_funnel is not None:
            for field_name in RETENTION_FUNNEL_FIELDS:
                metrics.retention_funnel[field_name] += retention_funnel[
                    field_name
                ]
    elif step == "snapshot":
        metrics.matches_evaluated += _safe_int(
            values.get("matches_evaluated")
        )
        metrics.snapshots_created += _safe_int(
            values.get("snapshots_created")
        )
        metrics.opportunities_generated += _safe_int(
            values.get("opportunities_generated")
        )
        metrics.no_bet_count += _safe_int(values.get("no_bet_count"))
        metrics.insufficient_data_count += _safe_int(
            values.get("insufficient_data_count")
        )
    elif step == "resolve":
        metrics.resolutions_created += _safe_int(values.get("inserted"))


def _record_failure(
    metrics: OperationMetrics,
    step: str,
    error_code: str,
) -> None:
    if step in {"daily_discovery", "daily_refresh"}:
        metrics.synchronization_failed += 1
    if error_code.startswith("provider_"):
        metrics.provider_error_count += 1
    if error_code == "postgresql_error":
        metrics.postgresql_error_count += 1


def _public_step_error(step: str, exc: Exception) -> str:
    if isinstance(exc, DailyOperationsRetentionFunnelError):
        return "retention_funnel_invalid"
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return "step_timeout"
    if isinstance(
        exc,
        (
            ApiFootballDisabledError,
            ApiFootballRequestError,
            SportsSyncConfigurationError,
        ),
    ):
        return "provider_unavailable"
    if isinstance(exc, SQLAlchemyError) or step in {
        "snapshot",
        "resolve",
        "report",
    }:
        return "postgresql_error"
    return "daily_operations_internal_error"


def _summary(
    *,
    correlation_id: str,
    target_date: date,
    started_at: datetime,
    status: str,
    error_code: str | None,
    step_results: list[dict[str, Any]],
    metrics: OperationMetrics,
) -> dict[str, Any]:
    return {
        "status": status,
        "correlation_id": correlation_id,
        "target_date": target_date.isoformat(),
        "started_at": started_at.isoformat(),
        "completed_at": utc_now().isoformat(),
        "error_code": error_code,
        "steps": step_results,
        "metrics": asdict(metrics),
        "bookmaker_calls": False,
        "odds_used": False,
        "betting_actions": False,
        "automatic_execution": False,
    }


def _event(summary: Mapping[str, Any], event: str) -> dict[str, Any]:
    return {
        "event": event,
        "correlation_id": summary.get("correlation_id"),
        "target_date": summary.get("target_date"),
        "status": summary.get("status"),
        "error_code": summary.get("error_code"),
    }


def _sanitize_saved_status(value: Mapping[str, Any]) -> dict[str, Any]:
    status = value.get("status")
    if status not in {"completed", "degraded", "failed"}:
        raise DailyOperationsUnavailable(
            "daily_operations_status_invalid"
        )
    correlation_id = value.get("correlation_id")
    target_date = value.get("target_date")
    started_at = value.get("started_at")
    completed_at = value.get("completed_at")
    if not all(
        isinstance(item, str) and 1 <= len(item) <= 64
        for item in (
            correlation_id,
            target_date,
            started_at,
            completed_at,
        )
    ):
        raise DailyOperationsUnavailable(
            "daily_operations_status_invalid"
        )
    raw_steps = value.get("steps")
    raw_metrics = value.get("metrics")
    if (
        not isinstance(raw_steps, list)
        or len(raw_steps) > 5
        or not isinstance(raw_metrics, Mapping)
    ):
        raise DailyOperationsUnavailable(
            "daily_operations_status_invalid"
        )
    steps: list[dict[str, Any]] = []
    allowed_steps = frozenset(STEP_TIMEOUTS)
    step_retention_funnel = {
        field_name: 0 for field_name in RETENTION_FUNNEL_FIELDS
    }
    for raw_step in raw_steps:
        if not isinstance(raw_step, Mapping):
            raise DailyOperationsUnavailable(
                "daily_operations_status_invalid"
            )
        name = raw_step.get("step")
        step_status = raw_step.get("status")
        if name not in allowed_steps or step_status not in {
            "completed",
            "failed",
        }:
            raise DailyOperationsUnavailable(
                "daily_operations_status_invalid"
            )
        safe_step: dict[str, Any] = {
            "step": name,
            "status": step_status,
            "critical": raw_step.get("critical") is True,
            "duration_ms": _safe_int(raw_step.get("duration_ms")),
        }
        error_code = raw_step.get("error_code")
        if isinstance(error_code, str) and error_code in {
            "step_timeout",
            "provider_unavailable",
            "postgresql_error",
            "retention_funnel_invalid",
            "daily_operations_internal_error",
        }:
            safe_step["error_code"] = error_code
        raw_step_metrics = raw_step.get("metrics")
        if isinstance(raw_step_metrics, Mapping):
            safe_step_metrics = _safe_step_metrics(
                str(name),
                raw_step_metrics,
            )
            safe_step["metrics"] = safe_step_metrics
            if (
                step_status == "completed"
                and name in {"daily_discovery", "daily_refresh"}
            ):
                for field_name in RETENTION_FUNNEL_FIELDS:
                    step_retention_funnel[field_name] += (
                        safe_step_metrics["retention_funnel"][field_name]
                    )
        elif (
            step_status == "completed"
            and name in {"daily_discovery", "daily_refresh"}
        ):
            raise DailyOperationsUnavailable(
                "daily_operations_status_invalid"
            )
        steps.append(safe_step)

    metrics = OperationMetrics()
    for field_name in (
        "synchronization_succeeded",
        "synchronization_failed",
        "fixtures_received",
        "fixtures_retained",
        "matches_evaluated",
        "snapshots_created",
        "resolutions_created",
        "opportunities_generated",
        "no_bet_count",
        "insufficient_data_count",
        "provider_error_count",
        "redis_fail_closed_count",
        "postgresql_error_count",
    ):
        setattr(metrics, field_name, _safe_int(raw_metrics.get(field_name)))
    metrics.quota_remaining_daily = _safe_optional_int(
        raw_metrics.get("quota_remaining_daily")
    )
    metrics.quota_remaining_minute = _safe_optional_int(
        raw_metrics.get("quota_remaining_minute")
    )
    raw_retention_funnel = raw_metrics.get("retention_funnel")
    safe_retention_funnel = _safe_retention_funnel(raw_retention_funnel)
    if (
        safe_retention_funnel is None
        or safe_retention_funnel["fixtures_received"]
        != metrics.fixtures_received
        or safe_retention_funnel["retained"]
        != metrics.fixtures_retained
        or safe_retention_funnel != step_retention_funnel
    ):
        raise DailyOperationsUnavailable(
            "daily_operations_status_invalid"
        )
    metrics.retention_funnel = safe_retention_funnel
    raw_durations = raw_metrics.get("step_duration_ms")
    if isinstance(raw_durations, Mapping):
        metrics.step_duration_ms = {
            str(name): _safe_int(duration)
            for name, duration in raw_durations.items()
            if name in allowed_steps
        }

    error_code = value.get("error_code")
    safe_error_code = (
        error_code
        if isinstance(error_code, str)
        and len(error_code) <= 80
        and error_code.replace("_", "").isalnum()
        else None
    )
    return {
        "status": status,
        "correlation_id": correlation_id,
        "target_date": target_date,
        "started_at": started_at,
        "completed_at": completed_at,
        "error_code": safe_error_code,
        "steps": steps,
        "metrics": asdict(metrics),
        "bookmaker_calls": False,
        "odds_used": False,
        "betting_actions": False,
        "automatic_execution": False,
    }


def _safe_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return 0
    return value


def _strict_nonnegative_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _safe_optional_int(value: object) -> int | None:
    if value is None:
        return None
    return _safe_int(value)


def _safe_retention_funnel(value: object) -> dict[str, int] | None:
    if not isinstance(value, Mapping):
        return None
    if set(value) != set(RETENTION_FUNNEL_FIELDS):
        return None
    if any(
        isinstance(value.get(field_name), bool)
        or not isinstance(value.get(field_name), int)
        or int(value.get(field_name, -1)) < 0
        for field_name in RETENTION_FUNNEL_FIELDS
    ):
        return None
    safe = {
        field_name: int(value[field_name])
        for field_name in RETENTION_FUNNEL_FIELDS
    }
    rejected = sum(
        count
        for field_name, count in safe.items()
        if field_name.startswith("rejected_")
    )
    if safe["fixtures_received"] != safe["retained"] + rejected:
        return None
    return safe


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "La date doit utiliser YYYY-MM-DD."
        ) from exc


def _emit_json(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _emit_public_error(code: str) -> None:
    print(
        json.dumps(
            {
                "status": "failed",
                "error": {"code": code},
                "bookmaker_calls": False,
                "betting_actions": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        file=sys.stderr,
    )


if __name__ == "__main__":
    raise SystemExit(main())
