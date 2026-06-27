from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_engine: Engine | None = None
_engine_url: str | None = None


def is_database_configured() -> bool:
    return bool(settings.database_url)


def get_database_status() -> str:
    if not is_database_configured():
        return "not_configured_phase_3"
    return "configured_not_checked_phase_3"


def get_engine() -> Engine:
    global _engine, _engine_url

    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required to create a database engine.")

    if _engine is None or _engine_url != settings.database_url:
        if _engine is not None:
            _engine.dispose()
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
        _engine_url = settings.database_url
        SessionLocal.configure(bind=_engine)

    return _engine


def create_database_engine() -> Engine:
    return get_engine()


def reset_database_engine() -> None:
    global _engine, _engine_url

    if _engine is not None:
        _engine.dispose()
    _engine = None
    _engine_url = None
    SessionLocal.configure(bind=None)


SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
