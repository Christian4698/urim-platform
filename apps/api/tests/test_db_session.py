from concurrent.futures import ThreadPoolExecutor
import warnings

import pytest
from sqlalchemy.exc import SADeprecationWarning, SAWarning

from app.core.config import settings
from app.db.session import (
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

    assert get_database_status() == "not_configured"
    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        get_engine()


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
