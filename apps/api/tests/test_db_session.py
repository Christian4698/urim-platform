import pytest

from app.core.config import settings
from app.db.session import get_database_status, get_db, get_engine, reset_database_engine


@pytest.fixture(autouse=True)
def clean_database_engine() -> None:
    reset_database_engine()
    yield
    reset_database_engine()


def test_database_status_does_not_open_connection_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "database_url", None)

    assert get_database_status() == "not_configured_phase_3"
    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        get_engine()


def test_get_engine_reuses_singleton_for_same_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "database_url", "sqlite+pysqlite:///:memory:")

    first_engine = get_engine()
    second_engine = get_engine()

    assert first_engine is second_engine

    db_generator = get_db()
    try:
        db = next(db_generator)
        assert db.bind is first_engine
    finally:
        db_generator.close()


def test_get_engine_recreates_engine_when_database_url_changes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    first_url = f"sqlite+pysqlite:///{(tmp_path / 'first.db').as_posix()}"
    second_url = f"sqlite+pysqlite:///{(tmp_path / 'second.db').as_posix()}"
    monkeypatch.setattr(settings, "database_url", first_url)
    first_engine = get_engine()

    monkeypatch.setattr(settings, "database_url", second_url)
    second_engine = get_engine()

    assert first_engine is not second_engine
    assert str(second_engine.url) == second_url
