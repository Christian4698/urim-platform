import importlib.util
import os
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic.config import Config
from sqlalchemy import create_engine

from app.db.models import metadata

REPO_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = REPO_ROOT / "apps" / "api" / "alembic.ini"
MIGRATION_FILE = (
    REPO_ROOT
    / "apps"
    / "api"
    / "alembic"
    / "versions"
    / "202606260001_phase_2_database_foundation.py"
)

REQUIRED_TABLES = {
    "app_users",
    "bankrolls",
    "bet_center_budgets",
    "tickets",
    "ticket_selections",
    "providers",
    "provider_capabilities",
    "provider_observations",
    "raw_payload_refs",
    "canonical_entities",
    "entity_mappings",
    "fixtures",
    "predictions",
    "prediction_versions",
    "feature_snapshots",
    "post_match_outcomes",
    "audit_logs",
    "incidents",
}


def test_alembic_config_loads_initial_revision() -> None:
    config = Config(str(ALEMBIC_INI))

    assert config.get_main_option("script_location").endswith("apps/api/alembic")
    assert MIGRATION_FILE.exists()

    spec = importlib.util.spec_from_file_location("phase_2_migration", MIGRATION_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.revision == "202606260001"
    assert module.down_revision is None


def test_metadata_declares_required_foundation_tables() -> None:
    assert REQUIRED_TABLES.issubset(set(metadata.tables))


def test_provider_observation_provenance_columns_exist() -> None:
    table = metadata.tables["provider_observations"]

    for column_name in (
        "provider",
        "provider_event_id",
        "observed_at",
        "available_at",
        "fetched_at",
        "source_version",
        "raw_hash",
        "quality_flags",
    ):
        assert column_name in table.c


def test_temporal_prediction_columns_exist() -> None:
    feature_snapshots = metadata.tables["feature_snapshots"]
    predictions = metadata.tables["predictions"]

    assert "as_of" in feature_snapshots.c
    assert "max_available_at" in feature_snapshots.c
    assert "prediction_time" in predictions.c
    assert "feature_snapshot_id" in predictions.c


def test_user_owned_tables_have_soft_delete_columns_only() -> None:
    user_owned_tables = {
        "app_users",
        "bankrolls",
        "bet_center_budgets",
        "tickets",
        "ticket_selections",
    }
    append_only_tables = {
        "predictions",
        "prediction_versions",
        "feature_snapshots",
        "provider_observations",
        "raw_payload_refs",
        "audit_logs",
        "post_match_outcomes",
    }

    for table_name in user_owned_tables:
        assert "deleted_at" in metadata.tables[table_name].c

    for table_name in append_only_tables:
        assert "deleted_at" not in metadata.tables[table_name].c


def test_migration_contains_append_only_and_temporal_triggers() -> None:
    migration_text = MIGRATION_FILE.read_text(encoding="utf-8")

    assert "prevent_append_only_mutation" in migration_text
    assert "enforce_prediction_snapshot_temporal_integrity" in migration_text
    assert "trg_predictions_temporal_integrity" in migration_text

    for table_name in (
        "predictions",
        "prediction_versions",
        "feature_snapshots",
        "provider_observations",
        "raw_payload_refs",
        "audit_logs",
        "post_match_outcomes",
    ):
        assert f"trg_{table_name}_append_only" in migration_text


def test_phase_two_disables_real_betting_by_schema_design() -> None:
    assert "real_betting_enabled" in metadata.tables["bankrolls"].c
    assert "real_betting_enabled" in metadata.tables["bet_center_budgets"].c
    assert "real_betting_enabled" in metadata.tables["ticket_selections"].c
    assert "is_real_bet" in metadata.tables["tickets"].c


def database_url_or_skip() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for PostgreSQL migration invariant tests.")
    return database_url


def test_postgresql_prediction_trigger_blocks_future_snapshot() -> None:
    engine = create_engine(database_url_or_skip())
    snapshot_id = uuid4()

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO feature_snapshots (
                        id,
                        as_of,
                        max_available_at,
                        feature_hash,
                        raw_hash,
                        immutable_hash
                    )
                    VALUES (
                        :snapshot_id,
                        TIMESTAMPTZ '2026-01-01 12:00:00+00',
                        TIMESTAMPTZ '2026-01-01 10:00:00+00',
                        :feature_hash,
                        :raw_hash,
                        :snapshot_hash
                    )
                    """
                ),
                {
                    "snapshot_id": snapshot_id,
                    "feature_hash": f"test-feature-{uuid4()}",
                    "raw_hash": f"test-raw-{uuid4()}",
                    "snapshot_hash": f"test-snapshot-{uuid4()}",
                },
            )

            with pytest.raises(sa.exc.DBAPIError):
                connection.execute(
                    sa.text(
                        """
                        INSERT INTO predictions (
                            prediction_id,
                            feature_snapshot_id,
                            model_version,
                            prediction_time,
                            market,
                            decision,
                            immutable_hash
                        )
                        VALUES (
                            :prediction_id,
                            :feature_snapshot_id,
                            'phase-2-test-model',
                            TIMESTAMPTZ '2026-01-01 09:00:00+00',
                            'test-market',
                            'NO_BET',
                            :immutable_hash
                        )
                        """
                    ),
                    {
                        "prediction_id": uuid4(),
                        "feature_snapshot_id": snapshot_id,
                        "immutable_hash": f"test-prediction-{uuid4()}",
                    },
                )
        finally:
            transaction.rollback()
            engine.dispose()


def test_postgresql_append_only_tables_reject_mutation() -> None:
    engine = create_engine(database_url_or_skip())
    audit_log_id = uuid4()

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO audit_logs (
                        id,
                        action,
                        resource_type
                    )
                    VALUES (
                        :audit_log_id,
                        'phase_2_insert_test',
                        'database_foundation_test'
                    )
                    """
                ),
                {"audit_log_id": audit_log_id},
            )

            with pytest.raises(sa.exc.DBAPIError):
                connection.execute(
                    sa.text(
                        """
                        UPDATE audit_logs
                        SET action = 'phase_2_mutation_test'
                        WHERE id = :audit_log_id
                        """
                    ),
                    {"audit_log_id": audit_log_id},
                )
        finally:
            transaction.rollback()
            engine.dispose()
