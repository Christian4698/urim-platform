from pathlib import Path

from sqlalchemy.dialects import postgresql

from app.db import models
from app.modules.sports_data.normalization import NormalizationResult
from app.modules.sports_data.repository import RESOURCE_TABLES, SportsRepository

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATION = (
    REPO_ROOT
    / "apps"
    / "api"
    / "alembic"
    / "versions"
    / "26fe26a73d5c_programme_b1_sports_data_foundation.py"
)
OBSERVATION_FIELDS = {
    "provider",
    "provider_event_id",
    "observed_at",
    "available_at",
    "fetched_at",
    "source_version",
    "quality_flags",
    "raw_hash",
    "freshness_status",
}


def test_program_b1_tables_cover_the_full_read_only_scope() -> None:
    assert set(RESOURCE_TABLES) == {
        "competitions",
        "seasons",
        "teams",
        "matches",
        "standings",
        "match_statistics",
        "match_events",
        "injuries",
        "lineups",
    }
    assert models.sports_sync_runs.name in models.metadata.tables
    assert models.sports_sync_errors.name in models.metadata.tables

    for table in RESOURCE_TABLES.values():
        assert OBSERVATION_FIELDS <= set(table.c.keys())
        assert "api_key" not in table.c
        assert "raw_payload" not in table.c
        assert "provider_url" not in table.c
        unique_columns = [
            {column.name for column in constraint.columns}
            for constraint in table.constraints
            if constraint.__class__.__name__ == "UniqueConstraint"
        ]
        assert {"provider", "provider_event_id", "raw_hash"} in unique_columns


def test_migration_enables_rls_redacts_data_api_roles_and_append_only_triggers() -> None:
    source = MIGRATION.read_text(encoding="utf-8")
    assert 'ENABLE ROW LEVEL SECURITY' in source
    assert "REVOKE ALL ON TABLE" in source
    assert "FROM anon" in source
    assert "FROM authenticated" in source
    assert "prevent_append_only_mutation" in source
    assert 'down_revision: str | Sequence[str] | None = "202607080035"' in source
    for table in (
        "api_football_competitions",
        "api_football_seasons",
        "api_football_teams",
        "api_football_matches",
        "api_football_standings",
        "api_football_match_statistics",
        "sports_sync_runs",
        "sports_sync_errors",
    ):
        assert table in source


def test_repository_uses_postgresql_on_conflict_for_idempotence() -> None:
    class Outcome:
        class ScalarRows:
            @staticmethod
            def all():
                return ["00000000-0000-0000-0000-000000000003"]

        @staticmethod
        def scalars():
            return Outcome.ScalarRows()

    class FakeSession:
        def __init__(self) -> None:
            self.statement = None

        def execute(self, statement):
            self.statement = statement
            return Outcome()

    session = FakeSession()
    repository = SportsRepository(session)
    row = {
        column.name: None
        for column in models.api_football_competitions.columns
        if column.name not in {"id", "provider_id", "sync_run_id", "created_at"}
    }
    row.update(
        {
            "provider": "api-football",
            "provider_event_id": "competition:39",
            "observed_at": "2026-07-23T10:00:00+00:00",
            "available_at": "2026-07-23T10:00:00+00:00",
            "fetched_at": "2026-07-23T10:00:00+00:00",
            "source_version": "football-v3",
            "quality_flags": [],
            "raw_hash": "a" * 64,
            "freshness_status": "fresh",
            "provider_competition_id": 39,
            "name": "Competition Test",
            "coverage": {},
        }
    )
    inserted, duplicate = repository.insert_result(
        NormalizationResult(resource="competitions", rows=(row,)),
        provider_id="00000000-0000-0000-0000-000000000001",
        run_id="00000000-0000-0000-0000-000000000002",
    )
    sql = str(
        session.statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    )
    assert inserted == 1
    assert duplicate == 0
    assert "ON CONFLICT DO NOTHING" in sql


def test_no_provider_secret_or_direct_provider_call_exists_in_frontend_or_blueprint() -> None:
    guarded_paths = [
        REPO_ROOT / "apps" / "web",
        REPO_ROOT / "render.yaml",
    ]
    for guarded_path in guarded_paths:
        paths = [guarded_path] if guarded_path.is_file() else guarded_path.rglob("*")
        for path in paths:
            if path.is_file() and not any(
                ignored in path.parts for ignored in (".next", "node_modules")
            ) and ".test." not in path.name:
                source = path.read_text(encoding="utf-8", errors="ignore")
                assert "API_FOOTBALL_KEY" not in source
                assert "x-apisports-key" not in source
                assert "v3.football.api-sports.io" not in source


def test_program_b1_keeps_prediction_bookmaker_live_and_betting_disabled() -> None:
    source = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "ENABLE_LIVE=false" in source
    assert "ENABLE_REAL_BETTING=false" in source
    assert "ALLOW_PRODUCTION_MOCKS=false" in source
    provider_source = (
        REPO_ROOT
        / "apps"
        / "api"
        / "app"
        / "modules"
        / "sports_data"
        / "provider.py"
    ).read_text(encoding="utf-8")
    assert '"odds"' in provider_source
    assert '"predictions"' in provider_source
    assert "FORBIDDEN_ENDPOINT_PARTS" in provider_source
