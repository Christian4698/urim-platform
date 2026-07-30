from __future__ import annotations

from datetime import UTC, datetime
import math
import os
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db import models
from app.db.isolation import (
    isolated_psycopg_url,
    validate_isolated_test_database,
)
from app.modules.kairos.repository import (
    KairosRepository,
    build_latest_as_of_subquery,
)
from app.api.v1.routes.kairos import (
    KAIROS_STATEMENT_TIMEOUT,
    POSTGRES_BIGINT_MAX,
    _configure_read_only_session,
)

API_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = API_ROOT / "alembic.ini"
MAX_REASONABLE_PLANNER_COST = 100_000


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
            "B1_TEST_DATABASE_URL is required for Kairos PostgreSQL tests."
        )
    if not result.safe:
        pytest.fail(
            "Kairos PostgreSQL test execution refused by isolation gate: "
            f"{result.reason}"
        )
    assert test_database_url is not None
    return isolated_psycopg_url(test_database_url)


@pytest.fixture
def postgres_engine() -> sa.Engine:
    engine = sa.create_engine(
        database_url_or_skip(),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )
    engine.url = sa.URL.create("postgresql+psycopg")
    try:
        yield engine
    finally:
        engine.dispose()


def test_isolated_database_is_at_alembic_head(
    postgres_engine: sa.Engine,
) -> None:
    expected_head = ScriptDirectory.from_config(
        Config(str(ALEMBIC_INI))
    ).get_current_head()
    with postgres_engine.connect() as connection:
        actual_heads = {
            row[0]
            for row in connection.execute(
                sa.text("SELECT version_num FROM alembic_version")
            )
        }

    assert actual_heads == {expected_head}


def test_kairos_transaction_is_read_only_and_statement_timeout_is_active(
    postgres_engine: sa.Engine,
) -> None:
    with Session(postgres_engine) as session:
        _configure_read_only_session(session)
        transaction_read_only = session.execute(
            sa.text("SHOW transaction_read_only")
        ).scalar_one()
        statement_timeout = session.execute(
            sa.text("SHOW statement_timeout")
        ).scalar_one()

    assert transaction_read_only == "on"
    assert statement_timeout in {"3s", KAIROS_STATEMENT_TIMEOUT}


def test_kairos_read_only_transaction_rejects_database_writes(
    postgres_engine: sa.Engine,
) -> None:
    with Session(postgres_engine) as session:
        _configure_read_only_session(session)
        with pytest.raises(sa.exc.DBAPIError):
            session.execute(
                sa.text(
                    "INSERT INTO audit_logs (action, resource_type) "
                    "VALUES ('kairos_forbidden_write', 'security_test')"
                )
            )
        session.rollback()


def test_kairos_repository_executes_real_bounded_postgresql_query(
    postgres_engine: sa.Engine,
) -> None:
    with Session(postgres_engine) as session:
        _configure_read_only_session(session)
        dataset = KairosRepository(session).load_match_dataset(
            POSTGRES_BIGINT_MAX,
            as_of=datetime.now(UTC),
            recent_window=5,
        )

    assert dataset is None


def test_kairos_target_query_indexes_and_planner_cost_are_reasonable(
    postgres_engine: sa.Engine,
) -> None:
    table = models.api_football_matches
    as_of = datetime.now(UTC)
    latest = build_latest_as_of_subquery(
        table,
        (table.c.provider_match_id,),
        as_of=as_of,
        scope_filters=(
            table.c.provider_match_id == POSTGRES_BIGINT_MAX,
        ),
    )
    statement = sa.select(latest).where(
        latest.c.observation_rank == 1,
        latest.c.provider_match_id == POSTGRES_BIGINT_MAX,
    )

    with postgres_engine.connect() as connection:
        indexes = {
            row[0]
            for row in connection.execute(
                sa.text(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = current_schema()
                      AND tablename = 'api_football_matches'
                    """
                )
            )
        }
        compiled = statement.compile(
            dialect=connection.dialect,
            compile_kwargs={"literal_binds": True},
        )
        plan_payload = connection.exec_driver_sql(
            f"EXPLAIN (FORMAT JSON, COSTS TRUE) {compiled}"
        ).scalar_one()

    assert "ix_api_football_matches_provider_id" in indexes
    assert "ix_api_football_matches_kickoff" in indexes
    assert "ix_api_football_matches_competition_season" in indexes
    total_cost = float(plan_payload[0]["Plan"]["Total Cost"])
    assert math.isfinite(total_cost)
    assert total_cost < MAX_REASONABLE_PLANNER_COST
