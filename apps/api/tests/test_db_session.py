from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import warnings

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SADeprecationWarning, SAWarning

import app.db.session as session_module
from app.core.config import settings
from app.db.session import (
    DATABASE_TIMEOUT_SECONDS,
    get_database_status,
    get_db,
    get_engine,
    get_session_factory,
    reset_database_engine,
)


@pytest.fixture(autouse=True)
def clean_database_engine() -> None:
    reset_database_engine()
    yield
    reset_database_engine()


def test_database_status_does_not_open_connection_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "database_url", None)

    assert get_database_status() == "unavailable"
    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        get_engine()


def test_database_status_executes_probe_when_database_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "database_url", "sqlite+pysqlite:///:memory:")

    assert get_database_status() == "ok"


def test_database_status_hides_connection_failure_details(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    secret = "DO_NOT_EXPOSE_DATABASE_SECRET"

    class FailingEngine:
        def connect(self):
            raise RuntimeError(f"connection failed for password={secret} host=db.internal.example")

    monkeypatch.setattr(settings, "database_url", "configured")
    monkeypatch.setattr(session_module, "get_engine", lambda: FailingEngine())

    assert get_database_status() == "unavailable"
    captured = capsys.readouterr()
    assert secret not in captured.out
    assert secret not in captured.err
    assert "db.internal.example" not in captured.out
    assert "db.internal.example" not in captured.err


def test_database_status_applies_postgresql_statement_timeout_before_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    statements: list[str] = []

    class ProbeResult:
        def scalar_one(self) -> int:
            return 1

    class ProbeConnection:
        dialect = SimpleNamespace(name="postgresql")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback) -> None:
            return None

        def exec_driver_sql(self, statement: str) -> None:
            statements.append(statement)

        def execute(self, statement):
            statements.append(str(statement))
            return ProbeResult()

    class ProbeEngine:
        def connect(self) -> ProbeConnection:
            return ProbeConnection()

    monkeypatch.setattr(settings, "database_url", "configured")
    monkeypatch.setattr(session_module, "get_engine", lambda: ProbeEngine())

    assert get_database_status() == "ok"
    assert statements == [
        "SET LOCAL statement_timeout = 3000",
        "SELECT 1",
    ]


def test_postgresql_engine_has_bounded_connection_and_pool_timeouts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_options: dict[str, object] = {}
    sqlite_engine = create_engine("sqlite+pysqlite:///:memory:")

    def capture_create_engine(database_url: str, **options: object):
        captured_options.update(options)
        return sqlite_engine

    monkeypatch.setattr(
        settings,
        "database_url",
        "postgresql+psycopg://user:password@db.internal.example:5432/urim",
    )
    monkeypatch.setattr(session_module, "create_engine", capture_create_engine)

    assert get_engine() is sqlite_engine
    assert captured_options["pool_timeout"] == DATABASE_TIMEOUT_SECONDS
    assert captured_options["connect_args"] == {
        "connect_timeout": DATABASE_TIMEOUT_SECONDS,
    }


def test_get_engine_and_session_factory_reuse_singletons_for_same_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "database_url", "sqlite+pysqlite:///:memory:")

    first_engine = get_engine()
    second_engine = get_engine()
    first_factory = get_session_factory()
    second_factory = get_session_factory()

    assert first_engine is second_engine
    assert first_factory is second_factory

    db_generator = get_db()
    try:
        db = next(db_generator)
        assert db.get_bind() is first_engine
    finally:
        db_generator.close()


def test_get_engine_and_session_factory_recreate_when_database_url_changes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    first_url = f"sqlite+pysqlite:///{(tmp_path / 'first.db').as_posix()}"
    second_url = f"sqlite+pysqlite:///{(tmp_path / 'second.db').as_posix()}"
    monkeypatch.setattr(settings, "database_url", first_url)
    first_engine = get_engine()
    first_factory = get_session_factory()

    monkeypatch.setattr(settings, "database_url", second_url)
    second_engine = get_engine()
    second_factory = get_session_factory()

    assert first_engine is not second_engine
    assert first_factory is not second_factory
    assert str(second_engine.url) == second_url

    with second_factory() as db:
        assert db.get_bind() is second_engine


def test_reset_database_engine_discards_singletons(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "database_url", "sqlite+pysqlite:///:memory:")
    first_engine = get_engine()
    first_factory = get_session_factory()

    reset_database_engine()

    second_engine = get_engine()
    second_factory = get_session_factory()

    assert first_engine is not second_engine
    assert first_factory is not second_factory


def test_missing_database_url_raises_when_session_factory_is_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "database_url", None)

    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        get_session_factory()


def test_concurrent_get_engine_calls_share_one_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "database_url", "sqlite+pysqlite:///:memory:")

    def engine_id() -> int:
        return id(get_engine())

    with ThreadPoolExecutor(max_workers=8) as executor:
        engine_ids = set(executor.map(lambda _: engine_id(), range(32)))

    assert len(engine_ids) == 1


def test_session_factory_operations_emit_no_sqlalchemy_warnings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "database_url", "sqlite+pysqlite:///:memory:")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        engine = get_engine()
        session_factory = get_session_factory()
        with session_factory() as db:
            assert db.get_bind() is engine

    sqlalchemy_warnings = [
        warning
        for warning in caught
        if issubclass(warning.category, (SADeprecationWarning, SAWarning))
    ]
    assert sqlalchemy_warnings == []
