from __future__ import annotations

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.db.models import api_football_fixture_staging, metadata


REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_FILE = (
    REPO_ROOT
    / "apps"
    / "api"
    / "alembic"
    / "versions"
    / "202607080035_phase_35_fixture_staging_db_schema.py"
)
DOC_PATH = REPO_ROOT / "docs" / "54_FIXTURE_STAGING_DB_SCHEMA.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "active"
    / "035-phase-35-fixture-staging-db-schema.md"
)
COMPLETED_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "035-phase-35-fixture-staging-db-schema.md"
)

EXPECTED_STAGING_COLUMNS = {
    "id",
    "provider",
    "provider_fixture_id",
    "provider_league_id",
    "provider_season",
    "fixture_date",
    "fixture_timezone",
    "fixture_status_short",
    "fixture_status_long",
    "home_team_provider_id",
    "home_team_name",
    "away_team_provider_id",
    "away_team_name",
    "goals_home",
    "goals_away",
    "score_halftime_home",
    "score_halftime_away",
    "score_fulltime_home",
    "score_fulltime_away",
    "payload_hash",
    "payload_top_level_keys",
    "fetched_at",
    "source_mode",
    "created_at",
    "updated_at",
}
FORBIDDEN_STAGING_COLUMNS = {
    "raw_payload",
    "odds",
    "bookmaker",
    "stake",
    "prediction",
    "betting",
}


def _migration_module() -> object:
    spec = importlib.util.spec_from_file_location("phase_35_migration", MIGRATION_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _model_source_slice() -> str:
    source = (REPO_ROOT / "apps" / "api" / "app" / "db" / "models.py").read_text(
        encoding="utf-8"
    )
    start = source.index("api_football_fixture_staging = sa.Table(")
    end = source.index("\n\nprovider_observations = sa.Table(", start)
    return source[start:end].lower()


def test_fixture_staging_migration_exists_and_has_revision_chain() -> None:
    module = _migration_module()

    assert MIGRATION_FILE.exists()
    assert module.revision == "202607080035"
    assert module.down_revision == "202606260001"


def test_fixture_staging_migration_creates_only_staging_schema() -> None:
    migration_text = MIGRATION_FILE.read_text(encoding="utf-8").lower()

    assert 'op.create_table(\n        "api_football_fixture_staging"' in migration_text
    assert "op.bulk_insert" not in migration_text
    assert ".insert(" not in migration_text
    assert 'op.create_table(\n        "predictions"' not in migration_text
    assert 'op.create_table(\n        "betting"' not in migration_text
    assert 'op.create_table(\n        "odds"' not in migration_text


def test_fixture_staging_metadata_declares_expected_columns_only() -> None:
    assert metadata.tables["api_football_fixture_staging"] is api_football_fixture_staging
    actual_columns = set(api_football_fixture_staging.c.keys())

    assert EXPECTED_STAGING_COLUMNS.issubset(actual_columns)
    assert FORBIDDEN_STAGING_COLUMNS.isdisjoint(actual_columns)


def test_fixture_staging_metadata_required_nullability_and_types() -> None:
    table = api_football_fixture_staging

    for column_name in (
        "provider",
        "provider_fixture_id",
        "payload_hash",
        "payload_top_level_keys",
        "fetched_at",
        "source_mode",
        "created_at",
    ):
        assert table.c[column_name].nullable is False

    assert table.c.provider_fixture_id.type.python_type is int
    assert table.c.provider_league_id.type.python_type is int
    assert table.c.provider_season.type.python_type is int
    assert table.c.payload_hash.type.length == 128
    assert isinstance(table.c.payload_top_level_keys.type, postgresql.JSONB)
    assert isinstance(table.c.fixture_date.type, sa.DateTime)
    assert isinstance(table.c.fetched_at.type, sa.DateTime)


def test_fixture_staging_metadata_constraints_and_indexes() -> None:
    table = api_football_fixture_staging
    unique_constraints = {
        constraint.name: tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, sa.UniqueConstraint)
    }
    indexes = {
        index.name: tuple(column.name for column in index.columns)
        for index in table.indexes
    }

    assert unique_constraints[
        "uq_api_football_fixture_staging_provider_fixture"
    ] == ("provider", "provider_fixture_id")
    assert indexes["ix_api_football_fixture_staging_provider_fixture_id"] == (
        "provider_fixture_id",
    )
    assert indexes["ix_api_football_fixture_staging_fixture_date"] == ("fixture_date",)
    assert indexes["ix_api_football_fixture_staging_league_season"] == (
        "provider_league_id",
        "provider_season",
    )
    assert indexes["ix_api_football_fixture_staging_status_short"] == (
        "fixture_status_short",
    )


def test_fixture_staging_model_slice_has_no_runtime_or_forbidden_logic() -> None:
    model_slice = _model_source_slice()

    forbidden_fragments = (
        "def ",
        "insert",
        "upsert",
        "ingest",
        "raw_payload",
        "odds",
        "bookmaker",
        "stake",
        "prediction",
        "betting",
    )
    for fragment in forbidden_fragments:
        assert fragment not in model_slice


def test_fixture_staging_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 35" in doc_text
    assert "no ingestion yet" in doc_lower
    assert "no real api call" in doc_lower
    assert "no prediction" in doc_lower
    assert "no betting/odds" in doc_lower
    assert "phase 36" in doc_lower
    assert "ingestion gate" in doc_lower
    assert "payload_hash is non-null" in doc_lower
    assert "raw_payload" not in doc_lower


def test_fixture_staging_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "54_FIXTURE_STAGING_DB_SCHEMA.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
