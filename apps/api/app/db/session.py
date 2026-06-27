from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def is_database_configured() -> bool:
    return bool(settings.database_url)


def get_database_status() -> str:
    if not is_database_configured():
        return "not_configured_phase_2"
    return "configured_not_checked_phase_2"


def create_database_engine() -> Engine:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required to create a database engine.")
    return create_engine(settings.database_url, pool_pre_ping=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    engine = create_database_engine()
    SessionLocal.configure(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
