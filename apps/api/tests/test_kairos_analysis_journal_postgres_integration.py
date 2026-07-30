from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import os
from threading import Barrier
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db import models
from app.db.isolation import (
    isolated_psycopg_url,
    validate_isolated_test_database,
)
from app.modules.kairos.journal import KairosJournalRepository
from app.modules.sports_data.repository import SportsRepository


def _database_url_or_skip() -> sa.URL:
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
            "B1_TEST_DATABASE_URL is required for B2.4 PostgreSQL tests."
        )
    if not result.safe:
        pytest.fail(
            "B2.4 PostgreSQL execution refused by isolation gate: "
            f"{result.reason}"
        )
    assert test_database_url is not None
    return isolated_psycopg_url(test_database_url)


@pytest.fixture(scope="module")
def postgres_engine() -> sa.Engine:
    engine = sa.create_engine(
        _database_url_or_skip(),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )
    engine.url = sa.URL.create("postgresql+psycopg")
    try:
        yield engine
    finally:
        engine.dispose()


def _hash(value: str) -> str:
    return sha256(value.encode()).hexdigest()


def _journal_row(
    *,
    analysis_id: UUID | None = None,
    provider_match_id: int | None = None,
    market: str = "SECOND_HALF_OVER_0_5",
    analysis_time: datetime | None = None,
    created_at: datetime | None = None,
    kickoff_at: datetime | None = None,
) -> dict[str, object]:
    now = datetime.now(UTC)
    resolved_analysis_id = analysis_id or uuid4()
    resolved_match_id = provider_match_id or uuid4().int % 1_000_000_000
    row: dict[str, object] = {
        "analysis_id": resolved_analysis_id,
        "provider_match_id": resolved_match_id,
        "kickoff_at": kickoff_at or now + timedelta(hours=2),
        "analysis_time": analysis_time or now - timedelta(minutes=1),
        "model_version": "kairos_half_time_b2_4_v1",
        "market": market,
        "estimated_probability": 0.75,
        "data_quality_score": 70,
        "technical_confidence_score": 55,
        "sample_size": 6,
        "safety_decision": "ANALYSIS_ALLOWED",
        "analysis_hash": _hash(f"analysis:{resolved_analysis_id}"),
        "analysis_payload": {
            "market": market,
            "provider_match_id": resolved_match_id,
        },
        "immutable_hash": _hash(f"immutable:{resolved_analysis_id}"),
    }
    if created_at is not None:
        row["created_at"] = created_at
    return row


def _resolution_row(
    journal_row: dict[str, object],
    *,
    outcome: str = "SUCCESS",
    provider_match_id: int | None = None,
    market: str | None = None,
    outcome_available_at: datetime | None = None,
    resolved_at: datetime | None = None,
    created_at: datetime | None = None,
    scores: tuple[int, int, int, int] = (0, 0, 1, 0),
) -> dict[str, object]:
    kickoff_at = journal_row["kickoff_at"]
    assert isinstance(kickoff_at, datetime)
    resolution_time = resolved_at or kickoff_at + timedelta(hours=2)
    halftime_home, halftime_away, fulltime_home, fulltime_away = scores
    analysis_id = journal_row["analysis_id"]
    row: dict[str, object] = {
        "analysis_id": analysis_id,
        "provider_match_id": (
            provider_match_id
            if provider_match_id is not None
            else journal_row["provider_match_id"]
        ),
        "market": market or str(journal_row["market"]),
        "outcome": outcome,
        "outcome_available_at": (
            outcome_available_at
            or kickoff_at + timedelta(hours=1, minutes=50)
        ),
        "resolved_at": resolution_time,
        "provider": "api-football",
        "provider_event_id": (
            f"fixture:{journal_row['provider_match_id']}"
        ),
        "source_version": "football-v3-test",
        "raw_hash": _hash(f"raw:{analysis_id}"),
        "outcome_payload": {
            "score_halftime_home": halftime_home,
            "score_halftime_away": halftime_away,
            "score_fulltime_home": fulltime_home,
            "score_fulltime_away": fulltime_away,
        },
        "immutable_hash": _hash(f"resolution:{analysis_id}:{outcome}"),
        "created_at": created_at or resolution_time,
    }
    return row


def _execute_failing(
    engine: sa.Engine,
    statement: sa.Executable,
) -> None:
    with engine.connect() as connection:
        transaction = connection.begin()
        with pytest.raises(sa.exc.DBAPIError):
            connection.execute(statement)
        transaction.rollback()


def test_b2_4_real_schema_has_expected_constraints_rls_and_privileges(
    postgres_engine: sa.Engine,
) -> None:
    expected_constraints = {
        "uq_kairos_analysis_journal_analysis_id",
        "uq_kairos_analysis_journal_immutable_hash",
        "uq_kairos_analysis_resolutions_analysis_id",
        "uq_kairos_analysis_resolutions_immutable_hash",
    }
    with postgres_engine.connect() as connection:
        constraints = set(
            connection.execute(
                sa.text(
                    """
                    SELECT conname
                    FROM pg_constraint
                    WHERE conrelid IN (
                        'kairos_analysis_journal'::regclass,
                        'kairos_analysis_resolutions'::regclass
                    )
                    """
                )
            ).scalars()
        )
        constraint_definitions = " ".join(
            connection.execute(
                sa.text(
                    """
                    SELECT pg_get_constraintdef(oid)
                    FROM pg_constraint
                    WHERE conrelid IN (
                        'kairos_analysis_journal'::regclass,
                        'kairos_analysis_resolutions'::regclass
                    )
                    """
                )
            ).scalars()
        )
        relations = connection.execute(
            sa.text(
                """
                SELECT relname, relrowsecurity
                FROM pg_class
                WHERE relname IN (
                    'kairos_analysis_journal',
                    'kairos_analysis_resolutions'
                )
                ORDER BY relname
                """
            )
        ).all()
        triggers = set(
            connection.execute(
                sa.text(
                    """
                    SELECT tgname
                    FROM pg_trigger
                    WHERE tgrelid IN (
                        'kairos_analysis_journal'::regclass,
                        'kairos_analysis_resolutions'::regclass
                    )
                      AND NOT tgisinternal
                    """
                )
            ).scalars()
        )
        public_role_grants = connection.execute(
            sa.text(
                """
                SELECT count(*)
                FROM information_schema.role_table_grants
                WHERE table_name IN (
                    'kairos_analysis_journal',
                    'kairos_analysis_resolutions'
                )
                  AND grantee IN ('anon', 'authenticated')
                """
            )
        ).scalar_one()
        required_identity_columns = connection.execute(
            sa.text(
                """
                SELECT column_name, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'kairos_analysis_resolutions'
                  AND column_name IN (
                      'analysis_id',
                      'provider_match_id',
                      'market'
                  )
                """
            )
        ).all()

    assert expected_constraints <= constraints
    assert "analysis_time <= created_at" in constraint_definitions
    assert "created_at < kickoff_at" in constraint_definitions
    assert "outcome_available_at <= resolved_at" in constraint_definitions
    assert "resolved_at <= created_at" in constraint_definitions
    assert "analysis_hash" in constraint_definitions
    assert "raw_hash" in constraint_definitions
    assert len(relations) == 2
    assert all(rls_enabled for _, rls_enabled in relations)
    assert {
        "trg_kairos_analysis_journal_append_only",
        "trg_kairos_analysis_resolutions_append_only",
        "trg_kairos_analysis_resolutions_integrity",
    } <= triggers
    assert public_role_grants == 0
    assert set(required_identity_columns) == {
        ("analysis_id", "NO"),
        ("provider_match_id", "NO"),
        ("market", "NO"),
    }


def test_b2_4_temporal_hash_uniqueness_and_append_only_are_enforced(
    postgres_engine: sa.Engine,
) -> None:
    now = datetime.now(UTC)
    future_analysis = _journal_row(
        analysis_time=now + timedelta(hours=1),
        kickoff_at=now + timedelta(hours=2),
    )
    _execute_failing(
        postgres_engine,
        models.kairos_analysis_journal.insert().values(future_analysis),
    )

    invalid_hash = _journal_row()
    invalid_hash["analysis_hash"] = "not-a-hash"
    _execute_failing(
        postgres_engine,
        models.kairos_analysis_journal.insert().values(invalid_hash),
    )

    original = _journal_row()
    with postgres_engine.begin() as connection:
        connection.execute(
            models.kairos_analysis_journal.insert().values(original)
        )

    duplicate_immutable = _journal_row()
    duplicate_immutable["immutable_hash"] = original["immutable_hash"]
    _execute_failing(
        postgres_engine,
        models.kairos_analysis_journal.insert().values(duplicate_immutable),
    )

    analysis_id = original["analysis_id"]
    _execute_failing(
        postgres_engine,
        models.kairos_analysis_journal.update()
        .where(models.kairos_analysis_journal.c.analysis_id == analysis_id)
        .values(estimated_probability=0.1),
    )
    _execute_failing(
        postgres_engine,
        models.kairos_analysis_journal.delete().where(
            models.kairos_analysis_journal.c.analysis_id == analysis_id
        ),
    )
    with postgres_engine.connect() as connection:
        persisted = connection.execute(
            sa.select(
                models.kairos_analysis_journal.c.estimated_probability,
                models.kairos_analysis_journal.c.analysis_payload,
                models.kairos_analysis_journal.c.immutable_hash,
            ).where(
                models.kairos_analysis_journal.c.analysis_id == analysis_id
            )
        ).one()

    assert float(persisted.estimated_probability) == 0.75
    assert persisted.analysis_payload == original["analysis_payload"]
    assert persisted.immutable_hash == original["immutable_hash"]


def test_b2_4_resolution_identity_timing_coherence_and_append_only(
    postgres_engine: sa.Engine,
) -> None:
    journal_row = _journal_row()
    with postgres_engine.begin() as connection:
        connection.execute(
            models.kairos_analysis_journal.insert().values(journal_row)
        )

    mismatched = _resolution_row(
        journal_row,
        provider_match_id=int(journal_row["provider_match_id"]) + 1,
    )
    _execute_failing(
        postgres_engine,
        models.kairos_analysis_resolutions.insert().values(mismatched),
    )

    kickoff_at = journal_row["kickoff_at"]
    assert isinstance(kickoff_at, datetime)
    premature = _resolution_row(
        journal_row,
        outcome_available_at=kickoff_at - timedelta(minutes=2),
        resolved_at=kickoff_at - timedelta(minutes=1),
        created_at=kickoff_at - timedelta(minutes=1),
    )
    _execute_failing(
        postgres_engine,
        models.kairos_analysis_resolutions.insert().values(premature),
    )

    incoherent = _resolution_row(
        journal_row,
        outcome="FAILURE",
        scores=(0, 0, 1, 0),
    )
    _execute_failing(
        postgres_engine,
        models.kairos_analysis_resolutions.insert().values(incoherent),
    )

    valid = _resolution_row(journal_row, scores=(0, 0, 1, 0))
    with postgres_engine.begin() as connection:
        connection.execute(
            models.kairos_analysis_resolutions.insert().values(valid)
        )

    analysis_id = journal_row["analysis_id"]
    _execute_failing(
        postgres_engine,
        models.kairos_analysis_resolutions.update()
        .where(
            models.kairos_analysis_resolutions.c.analysis_id == analysis_id
        )
        .values(outcome="FAILURE"),
    )
    _execute_failing(
        postgres_engine,
        models.kairos_analysis_resolutions.delete().where(
            models.kairos_analysis_resolutions.c.analysis_id == analysis_id
        ),
    )
    with postgres_engine.connect() as connection:
        outcome = connection.execute(
            sa.select(models.kairos_analysis_resolutions.c.outcome).where(
                models.kairos_analysis_resolutions.c.analysis_id
                == analysis_id
            )
        ).scalar_one()

    assert outcome == "SUCCESS"


def test_b2_4_snapshot_idempotence_has_stable_identity_without_overwrite(
    postgres_engine: sa.Engine,
) -> None:
    journal_row = _journal_row()
    statement = (
        pg_insert(models.kairos_analysis_journal)
        .values(journal_row)
        .on_conflict_do_nothing()
        .returning(models.kairos_analysis_journal.c.analysis_id)
    )
    with postgres_engine.begin() as connection:
        first = connection.execute(statement).scalar_one_or_none()
        second = connection.execute(statement).scalar_one_or_none()

    conflicting_payload = dict(journal_row)
    conflicting_payload["analysis_payload"] = {"tampered": True}
    conflicting_payload["immutable_hash"] = _hash(
        f"collision:{journal_row['analysis_id']}"
    )
    collision_statement = (
        pg_insert(models.kairos_analysis_journal)
        .values(conflicting_payload)
        .on_conflict_do_nothing()
        .returning(models.kairos_analysis_journal.c.analysis_id)
    )
    with postgres_engine.begin() as connection:
        collision = connection.execute(
            collision_statement
        ).scalar_one_or_none()
    with postgres_engine.connect() as connection:
        rows = connection.execute(
            sa.select(
                models.kairos_analysis_journal.c.analysis_id,
                models.kairos_analysis_journal.c.analysis_payload,
                models.kairos_analysis_journal.c.immutable_hash,
            ).where(
                models.kairos_analysis_journal.c.analysis_id
                == journal_row["analysis_id"]
            )
        ).all()

    assert first == journal_row["analysis_id"]
    assert second is None
    assert collision is None
    assert len(rows) == 1
    assert rows[0].analysis_payload == journal_row["analysis_payload"]
    assert rows[0].immutable_hash == journal_row["immutable_hash"]


def test_b2_4_concurrent_snapshot_is_single_and_error_rollback_recovers(
    postgres_engine: sa.Engine,
) -> None:
    concurrent_row = _journal_row()
    barrier = Barrier(2)

    def insert_snapshot() -> bool:
        statement = (
            pg_insert(models.kairos_analysis_journal)
            .values(concurrent_row)
            .on_conflict_do_nothing()
            .returning(models.kairos_analysis_journal.c.analysis_id)
        )
        with postgres_engine.begin() as connection:
            barrier.wait(timeout=5)
            return connection.execute(statement).scalar_one_or_none() is not None

    with ThreadPoolExecutor(max_workers=2) as executor:
        inserted = tuple(executor.map(lambda _: insert_snapshot(), range(2)))

    with postgres_engine.connect() as connection:
        count = connection.execute(
            sa.select(sa.func.count())
            .select_from(models.kairos_analysis_journal)
            .where(
                models.kairos_analysis_journal.c.analysis_id
                == concurrent_row["analysis_id"]
            )
        ).scalar_one()

    assert sorted(inserted) == [False, True]
    assert count == 1

    rolled_back_row = _journal_row()
    with postgres_engine.connect() as connection:
        transaction = connection.begin()
        connection.execute(
            models.kairos_analysis_journal.insert().values(rolled_back_row)
        )
        bad_resolution = _resolution_row(
            rolled_back_row,
            provider_match_id=(
                int(rolled_back_row["provider_match_id"]) + 1
            ),
        )
        with pytest.raises(sa.exc.DBAPIError):
            connection.execute(
                models.kairos_analysis_resolutions.insert().values(
                    bad_resolution
                )
            )
        transaction.rollback()

    with postgres_engine.connect() as connection:
        rolled_back_count = connection.execute(
            sa.select(sa.func.count())
            .select_from(models.kairos_analysis_journal)
            .where(
                models.kairos_analysis_journal.c.analysis_id
                == rolled_back_row["analysis_id"]
            )
        ).scalar_one()
    assert rolled_back_count == 0

    next_row = _journal_row()
    with postgres_engine.begin() as connection:
        inserted_id = connection.execute(
            models.kairos_analysis_journal.insert()
            .values(next_row)
            .returning(models.kairos_analysis_journal.c.analysis_id)
        ).scalar_one()
    assert inserted_id == next_row["analysis_id"]


def test_b2_4_full_snapshot_resolve_report_workflow_uses_valid_results_only(
    postgres_engine: sa.Engine,
) -> None:
    now = datetime.now(UTC)
    kickoff_at = now - timedelta(hours=3)
    journal_row = _journal_row(
        provider_match_id=uuid4().int % 1_000_000_000,
        market="SECOND_HALF_OVER_0_5",
        analysis_time=kickoff_at - timedelta(hours=1),
        created_at=kickoff_at - timedelta(minutes=30),
        kickoff_at=kickoff_at,
    )
    with postgres_engine.begin() as connection:
        connection.execute(
            models.kairos_analysis_journal.insert().values(journal_row)
        )
        unresolved = connection.execute(
            sa.select(sa.func.count())
            .select_from(models.kairos_analysis_resolutions)
            .where(
                models.kairos_analysis_resolutions.c.analysis_id
                == journal_row["analysis_id"]
            )
        ).scalar_one()
    assert unresolved == 0

    with Session(postgres_engine) as session:
        sports_repository = SportsRepository(session)
        provider_id = sports_repository.ensure_provider(enabled=True)
        run_id = sports_repository.start_run(
            provider_id=provider_id,
            sync_type="b2_4_postgres_workflow_test",
            scope={"mode": "TEST_ONLY"},
            started_at=now - timedelta(hours=1),
        )
        available_at = now - timedelta(minutes=30)
        session.execute(
            models.api_football_matches.insert().values(
                provider_id=provider_id,
                sync_run_id=run_id,
                provider="api-football",
                provider_event_id=(
                    f"fixture:{journal_row['provider_match_id']}"
                ),
                observed_at=available_at,
                available_at=available_at,
                fetched_at=available_at + timedelta(minutes=1),
                source_version="football-v3-test",
                quality_flags=["TEST_ONLY"],
                raw_hash=_hash(
                    f"match:{journal_row['provider_match_id']}"
                ),
                freshness_status="fresh",
                provider_match_id=journal_row["provider_match_id"],
                provider_competition_id=999_991,
                season=2026,
                kickoff_at=kickoff_at,
                timezone="UTC",
                status_short="FT",
                status_long="Match Finished",
                home_team_provider_id=999_992,
                home_team_name="TEST_ONLY Home",
                away_team_provider_id=999_993,
                away_team_name="TEST_ONLY Away",
                goals_home=1,
                goals_away=0,
                score_halftime_home=0,
                score_halftime_away=0,
                score_fulltime_home=1,
                score_fulltime_away=0,
            )
        )
        session.commit()

    resolve_as_of = datetime.now(UTC)
    with Session(postgres_engine) as session:
        journal_repository = KairosJournalRepository(session)
        summary = journal_repository.resolve_completed(as_of=resolve_as_of)
        session.commit()
    assert summary.inserted >= 1

    void_journal = _journal_row(market="HOME_OR_DRAW")
    void_resolution = _resolution_row(
        void_journal,
        outcome="VOID",
        scores=(0, 0, 0, 0),
    )
    with postgres_engine.begin() as connection:
        connection.execute(
            models.kairos_analysis_journal.insert().values(void_journal)
        )
        connection.execute(
            models.kairos_analysis_resolutions.insert().values(
                void_resolution
            )
        )

    with Session(postgres_engine) as session:
        metrics = KairosJournalRepository(session).resolved_metrics()
    with postgres_engine.connect() as connection:
        workflow_outcome = connection.execute(
            sa.select(models.kairos_analysis_resolutions.c.outcome).where(
                models.kairos_analysis_resolutions.c.analysis_id
                == journal_row["analysis_id"]
            )
        ).scalar_one()
        valid_resolution_count = connection.execute(
            sa.select(sa.func.count())
            .select_from(models.kairos_analysis_resolutions)
            .where(
                models.kairos_analysis_resolutions.c.outcome.in_(
                    ("SUCCESS", "FAILURE")
                )
            )
        ).scalar_one()
        all_resolution_count = connection.execute(
            sa.select(sa.func.count()).select_from(
                models.kairos_analysis_resolutions
            )
        ).scalar_one()

    resolved_metric_count = sum(
        metric.resolved_sample_size for metric in metrics.values()
    )
    assert workflow_outcome == "SUCCESS"
    assert resolved_metric_count == valid_resolution_count
    assert all_resolution_count > valid_resolution_count
    assert resolved_metric_count < 30
