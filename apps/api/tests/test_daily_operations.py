from __future__ import annotations

import asyncio
from datetime import date
import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.cli.daily_operations import (
    LOCK_KEY,
    STATUS_KEY,
    DailyOperationsOrchestrator,
    DailyOperationsUnavailable,
    OperationStep,
    RedisDailyOperationsGuard,
    build_parser,
)
from app.modules.sports_data.provider import ApiFootballDisabledError


class _FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.fail = False

    def set(
        self,
        name: str,
        value: str,
        *,
        nx: bool = False,
        ex: int | None = None,
    ) -> bool:
        del ex
        if self.fail:
            raise OSError("PRIVATE_REDIS_URL")
        if nx and name in self.values:
            return False
        self.values[name] = value
        return True

    def get(self, name: str) -> str | None:
        if self.fail:
            raise OSError("PRIVATE_REDIS_URL")
        return self.values.get(name)

    def eval(
        self,
        script: str,
        numkeys: int,
        *keys_and_args: object,
    ) -> int:
        del script, numkeys
        if self.fail:
            raise OSError("PRIVATE_REDIS_URL")
        key, token = keys_and_args
        if self.values.get(str(key)) != token:
            return 0
        del self.values[str(key)]
        return 1


def _step(
    name: str,
    *,
    critical: bool,
    runner,
    timeout: float = 1.0,
) -> OperationStep:
    return OperationStep(name, critical, timeout, runner)


def test_daily_operations_are_ordered_and_idempotently_repeatable() -> None:
    async def scenario() -> tuple[list[str], dict[str, Any], dict[str, Any]]:
        calls: list[str] = []

        def runner(name: str, result: dict[str, Any]):
            async def run(target_date: date) -> dict[str, Any]:
                assert target_date == date(2026, 7, 30)
                calls.append(name)
                return result

            return run

        steps = (
            _step(
                "daily_discovery",
                critical=True,
                runner=runner(
                    "daily_discovery",
                    {
                        "status": "SUCCEEDED",
                        "fixtures_received": 5,
                        "fixtures_retained": 3,
                    },
                ),
            ),
            _step(
                "daily_refresh",
                critical=False,
                runner=runner(
                    "daily_refresh",
                    {
                        "status": "SUCCEEDED",
                        "fixtures_received": 4,
                        "fixtures_retained": 3,
                    },
                ),
            ),
            _step(
                "snapshot",
                critical=True,
                runner=runner(
                    "snapshot",
                    {
                        "snapshots_created": 1,
                        "duplicate": 0,
                        "opportunities_generated": 1,
                        "no_bet_count": 2,
                        "insufficient_data_count": 0,
                    },
                ),
            ),
            _step(
                "resolve",
                critical=False,
                runner=runner(
                    "resolve",
                    {"inserted": 1, "duplicate": 0},
                ),
            ),
            _step(
                "report",
                critical=False,
                runner=runner(
                    "report",
                    {
                        "performance": {
                            "total_snapshots": 1,
                            "resolved": 1,
                            "unresolved": 0,
                            "void": 0,
                            "resolved_sample_size": 1,
                            "sample_status": "insufficient_sample",
                        }
                    },
                ),
            ),
        )
        redis = _FakeRedis()
        orchestrator = DailyOperationsOrchestrator(
            guard=RedisDailyOperationsGuard(client=redis),
            steps=steps,
            emit=lambda event: None,
        )
        first = await orchestrator.run(date(2026, 7, 30))
        second = await orchestrator.run(date(2026, 7, 30))
        return calls, first, second

    calls, first, second = asyncio.run(scenario())

    expected_order = [
        "daily_discovery",
        "daily_refresh",
        "snapshot",
        "resolve",
        "report",
    ]
    assert calls == [*expected_order, *expected_order]
    assert first["status"] == "completed"
    assert second["status"] == "completed"
    assert first["metrics"]["snapshots_created"] == 1
    assert second["metrics"]["snapshots_created"] == 1
    assert first["bookmaker_calls"] is False
    assert first["betting_actions"] is False


def test_daily_operations_cli_contract_and_entrypoint() -> None:
    run_args = build_parser().parse_args(["--date", "2026-07-30"])
    status_args = build_parser().parse_args(["status"])
    project = Path("pyproject.toml").read_text(encoding="utf-8")

    assert run_args.command == "run"
    assert run_args.date == date(2026, 7, 30)
    assert status_args.command == "status"
    assert status_args.date is None
    assert (
        'urim-daily-operations = "app.cli.daily_operations:main"'
        in project
    )


def test_b2_4_1_runbook_covers_safe_operations_and_rollback() -> None:
    runbook = Path(
        "../../docs/79_B2_4_1_KAIROS_OPERATIONS_RUNBOOK.md"
    ).read_text(encoding="utf-8")

    for required in (
        "urim-daily-operations --date YYYY-MM-DD",
        "urim-daily-operations status",
        "Interprétation de zéro opportunité",
        "Panne fournisseur",
        "Panne Redis",
        "Panne PostgreSQL",
        "Contrôle des quotas",
        "Rotation de secrets",
        "Rollback applicatif sans downgrade DB",
        "Aucun downgrade de base de production",
    ):
        assert required in runbook


def test_distributed_lock_refuses_simultaneous_run() -> None:
    async def scenario() -> tuple[dict[str, Any], dict[str, Any]]:
        started = asyncio.Event()
        finish = asyncio.Event()

        async def blocking_runner(target_date: date) -> dict[str, Any]:
            del target_date
            started.set()
            await finish.wait()
            return {"status": "SUCCEEDED"}

        redis = _FakeRedis()
        steps = (
            _step(
                "daily_discovery",
                critical=True,
                runner=blocking_runner,
            ),
        )
        first_orchestrator = DailyOperationsOrchestrator(
            guard=RedisDailyOperationsGuard(client=redis),
            steps=steps,
            emit=lambda event: None,
        )
        second_orchestrator = DailyOperationsOrchestrator(
            guard=RedisDailyOperationsGuard(client=redis),
            steps=steps,
            emit=lambda event: None,
        )
        first_task = asyncio.create_task(
            first_orchestrator.run(date(2026, 7, 30))
        )
        await started.wait()
        second = await second_orchestrator.run(date(2026, 7, 30))
        finish.set()
        first = await first_task
        return first, second

    first, second = asyncio.run(scenario())

    assert first["status"] == "completed"
    assert second["status"] == "failed"
    assert second["error_code"] == "daily_operations_already_running"
    assert second["metrics"]["redis_fail_closed_count"] == 1


def test_provider_failure_is_critical_and_stops_following_steps() -> None:
    async def scenario() -> tuple[list[str], dict[str, Any]]:
        calls: list[str] = []

        async def provider_failure(target_date: date) -> dict[str, Any]:
            del target_date
            calls.append("daily_discovery")
            raise ApiFootballDisabledError("PRIVATE_PROVIDER_KEY")

        async def forbidden(target_date: date) -> dict[str, Any]:
            del target_date
            calls.append("snapshot")
            return {}

        orchestrator = DailyOperationsOrchestrator(
            guard=RedisDailyOperationsGuard(client=_FakeRedis()),
            steps=(
                _step(
                    "daily_discovery",
                    critical=True,
                    runner=provider_failure,
                ),
                _step("snapshot", critical=True, runner=forbidden),
            ),
            emit=lambda event: None,
        )
        return calls, await orchestrator.run(date(2026, 7, 30))

    calls, summary = asyncio.run(scenario())

    assert calls == ["daily_discovery"]
    assert summary["status"] == "failed"
    assert summary["error_code"] == "provider_unavailable"
    assert summary["metrics"]["provider_error_count"] == 1


def test_postgresql_failure_stops_after_snapshot_without_secret_leak() -> None:
    events: list[dict[str, Any]] = []

    async def scenario() -> dict[str, Any]:
        async def snapshot_failure(target_date: date) -> dict[str, Any]:
            del target_date
            raise SQLAlchemyError(
                "DATABASE_URL=postgresql://private-credential"
            )

        async def forbidden(target_date: date) -> dict[str, Any]:
            del target_date
            pytest.fail("critical failure must stop the workflow")

        orchestrator = DailyOperationsOrchestrator(
            guard=RedisDailyOperationsGuard(client=_FakeRedis()),
            steps=(
                _step("snapshot", critical=True, runner=snapshot_failure),
                _step("resolve", critical=False, runner=forbidden),
            ),
            emit=events.append,
        )
        return await orchestrator.run(date(2026, 7, 30))

    summary = asyncio.run(scenario())
    serialized = json.dumps({"summary": summary, "events": events})

    assert summary["status"] == "failed"
    assert summary["error_code"] == "postgresql_error"
    assert summary["metrics"]["postgresql_error_count"] == 1
    assert "private-credential" not in serialized.lower()
    assert "database_url" not in serialized.lower()


def test_non_critical_refresh_failure_continues_with_explicit_degradation() -> None:
    async def scenario() -> tuple[list[str], dict[str, Any]]:
        calls: list[str] = []

        async def refresh_failure(target_date: date) -> dict[str, Any]:
            del target_date
            calls.append("daily_refresh")
            raise RuntimeError("PRIVATE_PROVIDER_RESPONSE")

        async def snapshot(target_date: date) -> dict[str, Any]:
            del target_date
            calls.append("snapshot")
            return {"snapshots_created": 0}

        orchestrator = DailyOperationsOrchestrator(
            guard=RedisDailyOperationsGuard(client=_FakeRedis()),
            steps=(
                _step(
                    "daily_refresh",
                    critical=False,
                    runner=refresh_failure,
                ),
                _step("snapshot", critical=True, runner=snapshot),
            ),
            emit=lambda event: None,
        )
        return calls, await orchestrator.run(date(2026, 7, 30))

    calls, summary = asyncio.run(scenario())

    assert calls == ["daily_refresh", "snapshot"]
    assert summary["status"] == "degraded"
    assert summary["steps"][0]["status"] == "failed"
    assert summary["steps"][1]["status"] == "completed"


def test_step_timeout_is_bounded_and_stops_when_critical() -> None:
    async def scenario() -> dict[str, Any]:
        async def slow_step(target_date: date) -> dict[str, Any]:
            del target_date
            await asyncio.sleep(0.05)
            return {}

        orchestrator = DailyOperationsOrchestrator(
            guard=RedisDailyOperationsGuard(client=_FakeRedis()),
            steps=(
                _step(
                    "snapshot",
                    critical=True,
                    runner=slow_step,
                    timeout=0.001,
                ),
            ),
            emit=lambda event: None,
        )
        return await orchestrator.run(date(2026, 7, 30))

    summary = asyncio.run(scenario())

    assert summary["status"] == "failed"
    assert summary["error_code"] == "step_timeout"
    assert summary["steps"][0]["duration_ms"] >= 0


def test_redis_failure_is_fail_closed_before_any_step() -> None:
    redis = _FakeRedis()
    redis.fail = True
    orchestrator = DailyOperationsOrchestrator(
        guard=RedisDailyOperationsGuard(client=redis),
        steps=(),
        emit=lambda event: None,
    )

    with pytest.raises(
        DailyOperationsUnavailable,
        match="daily_operations_redis_unavailable",
    ):
        asyncio.run(orchestrator.run(date(2026, 7, 30)))


def test_status_output_ignores_untrusted_extra_fields() -> None:
    redis = _FakeRedis()
    guard = RedisDailyOperationsGuard(client=redis)
    summary = {
        "status": "completed",
        "correlation_id": "12345678-1234-1234-1234-123456789012",
        "target_date": "2026-07-30",
        "started_at": "2026-07-30T00:00:00+00:00",
        "completed_at": "2026-07-30T00:01:00+00:00",
        "error_code": None,
        "steps": [],
        "metrics": {},
        "DATABASE_URL": "postgresql://private-credential",
    }
    redis.values[STATUS_KEY] = json.dumps(summary)
    redis.values[LOCK_KEY] = "unrelated"

    status = guard.read_status()
    serialized = json.dumps(status)

    assert status is not None
    assert status["status"] == "completed"
    assert "DATABASE_URL" not in serialized
    assert "private-credential" not in serialized
