import os
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db.isolation import (
    isolated_psycopg_url,
    validate_isolated_test_database,
)
from app.db import models
from app.modules.sports_data.normalization import NormalizationResult
from app.modules.sports_data.repository import SportsRepository

def database_url_or_skip() -> sa.URL:
    test_database_url = os.environ.get("B1_TEST_DATABASE_URL")
    if "DATABASE_URL" in os.environ:
        pytest.fail("DATABASE_URL must be absent for PostgreSQL tests.")
    result = validate_isolated_test_database(
        test_database_url,
        database_url=None,
        app_env=os.environ.get("APP_ENV"),
    )
    if result.reason == "B1_TEST_DATABASE_URL_MISSING":
        pytest.skip(
            "B1_TEST_DATABASE_URL is required for PostgreSQL integration "
            "tests."
        )
    if not result.safe:
        pytest.fail(
            "PostgreSQL test execution refused by isolation gate: "
            f"{result.reason}"
        )
    assert test_database_url is not None
    return isolated_psycopg_url(test_database_url)


def test_migrations_rls_append_only_and_idempotence_on_postgresql() -> None:
    engine = sa.create_engine(database_url_or_skip())
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            session = Session(bind=connection)
            repository = SportsRepository(session)
            provider_id = repository.ensure_provider(enabled=True)
            now = datetime.now(UTC)
            run_id = repository.start_run(
                provider_id=provider_id,
                sync_type="integration_test",
                scope={"mode": "TEST_ONLY"},
                started_at=now,
            )
            row = {
                "provider": "api-football",
                "provider_event_id": "competition:999999",
                "observed_at": now,
                "available_at": now,
                "fetched_at": now,
                "source_version": "football-v3-test",
                "quality_flags": ["TEST_ONLY"],
                "raw_hash": "f" * 64,
                "freshness_status": "fresh",
                "provider_competition_id": 999999,
                "name": "TEST_ONLY Competition",
                "kind": "League",
                "country_name": None,
                "country_code": None,
                "current_season": 2026,
                "coverage": {},
            }
            result = NormalizationResult(
                resource="competitions",
                rows=(row,),
            )
            assert repository.insert_result(
                result,
                provider_id=provider_id,
                run_id=run_id,
            ) == (1, 0)
            assert repository.insert_result(
                result,
                provider_id=provider_id,
                run_id=run_id,
            ) == (0, 1)
            count = connection.execute(
                sa.select(sa.func.count())
                .select_from(models.api_football_competitions)
                .where(
                    models.api_football_competitions.c.provider_event_id
                    == "competition:999999",
                    models.api_football_competitions.c.raw_hash == "f" * 64,
                )
            ).scalar_one()
            assert count == 1

            rls_rows = connection.execute(
                sa.text(
                    """
                    SELECT relname, relrowsecurity
                    FROM pg_class
                    WHERE relname = ANY(:tables)
                    """
                ),
                {
                    "tables": [
                        "api_football_competitions",
                        "api_football_matches",
                        "sports_sync_runs",
                        "sports_sync_errors",
                    ]
                },
            ).all()
            assert len(rls_rows) == 4
            assert all(enabled is True for _, enabled in rls_rows)

            trigger_count = connection.execute(
                sa.text(
                    """
                    SELECT count(*)
                    FROM pg_trigger
                    WHERE tgname = 'trg_api_football_competitions_append_only'
                      AND NOT tgisinternal
                    """
                )
            ).scalar_one()
            assert trigger_count == 1
        finally:
            transaction.rollback()
            engine.dispose()
