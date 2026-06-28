from collections.abc import Generator
from threading import RLock

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.constants import DATABASE_CONFIGURED_NOT_CHECKED, DATABASE_NOT_CONFIGURED

_engine_lock = RLock()
_engine: Engine | None = None
_engine_url: str | None = None
_session_factory: sessionmaker[Session] | None = None


def is_database_configured() -> bool:
    return bool(settings.database_url)


def get_database_status() -> str:
    if not is_database_configured():
        return DATABASE_NOT_CONFIGURED
    return DATABASE_CONFIGURED_NOT_CHECKED


def get_engine() -> Engine:
    engine, _ = _get_engine_and_session_factory()
    return engine


def get_session_factory() -> sessionmaker[Session]:
    _, factory = _get_engine_and_session_factory()
    return factory


def _get_engine_and_session_factory() -> tuple[Engine, sessionmaker[Session]]:
    global _engine, _engine_url, _session_factory

    with _engine_lock:
        database_url = settings.database_url
        if not database_url:
            raise RuntimeError("DATABASE_URL is required to create a database engine.")

        if _engine is None or _engine_url != database_url:
            if _engine is not None:
                _engine.dispose()
            _engine = create_engine(database_url, pool_pre_ping=True)
            _engine_url = database_url
            _session_factory = sessionmaker(_engine, autoflush=False, expire_on_commit=False)
        elif _session_factory is None:
            _session_factory = sessionmaker(_engine, autoflush=False, expire_on_commit=False)

        return _engine, _session_factory


def create_database_engine() -> Engine:
    return get_engine()


def reset_database_engine() -> None:
    global _engine, _engine_url, _session_factory

    with _engine_lock:
        if _engine is not None:
            _engine.dispose()
        _engine = None
        _engine_url = None
        _session_factory = None


def get_db() -> Generator[Session, None, None]:
    session_factory = get_session_factory()
    with session_factory() as db:
        yield db
