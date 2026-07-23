import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from app.modules.sports_data.provider import (
    ApiFootballRequestError,
    ApiFootballEnvelope,
    ApiFootballEnvelopeModel,
)
from app.modules.sports_data.sync import RequestSpec, SportsSyncService


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeClient:
    enabled = True
    request_count = 1
    quota_remaining_daily = 99
    quota_remaining_minute = 9

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def get(self, endpoint: str, _params: object) -> ApiFootballEnvelope:
        now = datetime.now(UTC)
        return ApiFootballEnvelope(
            endpoint=endpoint,
            request_id="TEST_ONLY",
            fetched_at=now,
            observed_at=now,
            available_at=now,
            source_version="football-v3-test",
            raw_hash="a" * 64,
            quota_limit_daily=100,
            quota_remaining_daily=99,
            quota_limit_minute=10,
            quota_remaining_minute=9,
            data=ApiFootballEnvelopeModel(
                get=endpoint,
                parameters={},
                errors=[],
                results=1,
                paging={"current": 1, "total": 1},
                response=[{"TEST_ONLY": True}],
            ),
        )


class FailingClient(FakeClient):
    def __init__(self) -> None:
        self.endpoints: list[str] = []

    async def get(self, endpoint: str, _params: object) -> ApiFootballEnvelope:
        self.endpoints.append(endpoint)
        raise ApiFootballRequestError("PUBLIC_SAFE", retryable=True)


class FakeRepository:
    def __init__(self) -> None:
        self.run_id = uuid4()
        self.errors: list[str] = []
        self.finished: dict[str, object] | None = None

    def ensure_provider(self, *, enabled: bool):
        assert enabled is True
        return uuid4()

    def start_run(self, **_kwargs: object):
        return self.run_id

    def record_error(self, **kwargs: object) -> None:
        self.errors.append(str(kwargs["error_code"]))

    def finish_run(self, **kwargs: object) -> None:
        self.finished = dict(kwargs)


def test_unexpected_sync_failure_is_neutralized_and_run_is_closed() -> None:
    session = FakeSession()
    service = SportsSyncService(session, client=FakeClient())  # type: ignore[arg-type]
    repository = FakeRepository()
    service.repository = repository  # type: ignore[assignment]

    def fail_normalization(_envelope: ApiFootballEnvelope):
        raise KeyError("PRIVATE_PROVIDER_FIELD")

    summary = asyncio.run(
        service._run(
            "test_failure",
            {"mode": "TEST_ONLY"},
            [
                RequestSpec(
                    endpoint="leagues",
                    params={"id": 39},
                    normalize=fail_normalization,
                )
            ],
        )
    )

    assert session.rollbacks == 1
    assert repository.errors == ["synchronization_internal_error"]
    assert repository.finished is not None
    assert repository.finished["status"] == "FAILED"
    assert summary.status == "FAILED"
    assert summary.public_error_code == "synchronization_internal_error"


def test_statistics_style_run_stops_after_error_for_safe_resume() -> None:
    session = FakeSession()
    client = FailingClient()
    service = SportsSyncService(session, client=client)  # type: ignore[arg-type]
    repository = FakeRepository()
    service.repository = repository  # type: ignore[assignment]

    summary = asyncio.run(
        service._run(
            "test_resume",
            {"mode": "TEST_ONLY"},
            [
                RequestSpec(
                    endpoint="fixtures/events",
                    params={"fixture": 10},
                    normalize=lambda _envelope: (),
                ),
                RequestSpec(
                    endpoint="fixtures/statistics",
                    params={"fixture": 10},
                    normalize=lambda _envelope: (),
                ),
            ],
            stop_on_error=True,
        )
    )

    assert client.endpoints == ["fixtures/events"]
    assert repository.errors == ["provider_unavailable"]
    assert summary.status == "FAILED"
