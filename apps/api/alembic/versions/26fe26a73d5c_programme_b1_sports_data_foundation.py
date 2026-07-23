"""programme b1 sports data foundation

Revision ID: 26fe26a73d5c
Revises: 202607080035
Create Date: 2026-07-23 12:02:28+00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import SchemaItem

revision: str = "26fe26a73d5c"
down_revision: str | Sequence[str] | None = "202607080035"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_TABLES = (
    "sports_sync_runs",
    "sports_sync_errors",
    "api_football_competitions",
    "api_football_seasons",
    "api_football_teams",
    "api_football_matches",
    "api_football_standings",
    "api_football_match_statistics",
    "api_football_match_events",
    "api_football_injuries",
    "api_football_lineups",
)
APPEND_ONLY_TABLES = NEW_TABLES[1:]
EXISTING_PUBLIC_TABLES = (
    "app_users",
    "bankrolls",
    "bet_center_budgets",
    "providers",
    "provider_capabilities",
    "canonical_entities",
    "fixtures",
    "tickets",
    "entity_mappings",
    "raw_payload_refs",
    "api_football_fixture_staging",
    "provider_observations",
    "feature_snapshots",
    "predictions",
    "prediction_versions",
    "ticket_selections",
    "post_match_outcomes",
    "audit_logs",
    "incidents",
)


def uuid_pk() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def created_at() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


def jsonb(
    name: str,
    *,
    default: str = "'{}'::jsonb",
    nullable: bool = False,
) -> sa.Column:
    return sa.Column(
        name,
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=nullable,
        server_default=sa.text(default) if default else None,
    )


def observation_columns(table_name: str) -> list[SchemaItem]:
    return [
        sa.Column(
            "provider_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("providers.id"),
            nullable=False,
        ),
        sa.Column(
            "sync_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_sync_runs.id"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("provider_event_id", sa.String(length=240), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_version", sa.String(length=80), nullable=False),
        jsonb("quality_flags", default="'[]'::jsonb"),
        sa.Column("raw_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "freshness_status",
            sa.String(length=32),
            nullable=False,
            server_default="fresh",
        ),
        created_at(),
        sa.CheckConstraint(
            "observed_at <= available_at AND available_at <= fetched_at",
            name=f"ck_{table_name}_temporal_order",
        ),
        sa.CheckConstraint(
            "freshness_status IN ('fresh', 'stale', 'unknown')",
            name=f"ck_{table_name}_freshness_status",
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_event_id",
            "raw_hash",
            name=f"uq_{table_name}_observation",
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "sports_sync_runs",
        uuid_pk(),
        sa.Column(
            "provider_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("providers.id"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("sync_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        jsonb("scope"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_duplicate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quota_limit_daily", sa.Integer(), nullable=True),
        sa.Column("quota_remaining_daily", sa.Integer(), nullable=True),
        sa.Column("quota_limit_minute", sa.Integer(), nullable=True),
        sa.Column("quota_remaining_minute", sa.Integer(), nullable=True),
        jsonb("checkpoint"),
        sa.Column("public_error_code", sa.String(length=80), nullable=True),
        created_at(),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('RUNNING', 'SUCCEEDED', 'PARTIAL', 'FAILED')",
            name="ck_sports_sync_runs_status",
        ),
        sa.CheckConstraint(
            "request_count >= 0 AND records_received >= 0 AND records_inserted >= 0 "
            "AND records_duplicate >= 0 AND records_rejected >= 0",
            name="ck_sports_sync_runs_counters_non_negative",
        ),
    )
    op.create_table(
        "sports_sync_errors",
        uuid_pk(),
        sa.Column(
            "sync_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sports_sync_runs.id"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("endpoint", sa.String(length=80), nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=False),
        sa.Column("public_message", sa.String(length=240), nullable=False),
        sa.Column(
            "retryable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        jsonb("context"),
        created_at(),
        sa.CheckConstraint(
            "attempt >= 1",
            name="ck_sports_sync_errors_attempt_positive",
        ),
    )
    op.create_table(
        "api_football_competitions",
        uuid_pk(),
        *observation_columns("api_football_competitions"),
        sa.Column("provider_competition_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("kind", sa.String(length=80), nullable=True),
        sa.Column("country_name", sa.String(length=160), nullable=True),
        sa.Column("country_code", sa.String(length=8), nullable=True),
        sa.Column("current_season", sa.Integer(), nullable=True),
        jsonb("coverage"),
    )
    op.create_table(
        "api_football_seasons",
        uuid_pk(),
        *observation_columns("api_football_seasons"),
        sa.Column("provider_competition_id", sa.BigInteger(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=True),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column(
            "is_current",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        jsonb("coverage"),
        sa.CheckConstraint(
            "year BETWEEN 1900 AND 2100",
            name="ck_api_football_seasons_year",
        ),
        sa.CheckConstraint(
            "ends_on IS NULL OR starts_on IS NULL OR ends_on >= starts_on",
            name="ck_api_football_seasons_date_order",
        ),
    )
    op.create_table(
        "api_football_teams",
        uuid_pk(),
        *observation_columns("api_football_teams"),
        sa.Column("provider_team_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=160), nullable=True),
        sa.Column("founded", sa.Integer(), nullable=True),
        sa.Column("is_national", sa.Boolean(), nullable=True),
        sa.Column("venue_provider_id", sa.BigInteger(), nullable=True),
        sa.Column("venue_name", sa.String(length=240), nullable=True),
        sa.Column("venue_city", sa.String(length=160), nullable=True),
        sa.Column("venue_capacity", sa.Integer(), nullable=True),
    )
    op.create_table(
        "api_football_matches",
        uuid_pk(),
        *observation_columns("api_football_matches"),
        sa.Column("provider_match_id", sa.BigInteger(), nullable=False),
        sa.Column("provider_competition_id", sa.BigInteger(), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("kickoff_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("status_short", sa.String(length=40), nullable=False),
        sa.Column("status_long", sa.String(length=120), nullable=False),
        sa.Column("elapsed", sa.Integer(), nullable=True),
        sa.Column("round", sa.String(length=160), nullable=True),
        sa.Column("venue_name", sa.String(length=240), nullable=True),
        sa.Column("venue_city", sa.String(length=160), nullable=True),
        sa.Column("home_team_provider_id", sa.BigInteger(), nullable=False),
        sa.Column("home_team_name", sa.String(length=240), nullable=False),
        sa.Column("away_team_provider_id", sa.BigInteger(), nullable=False),
        sa.Column("away_team_name", sa.String(length=240), nullable=False),
        sa.Column("goals_home", sa.Integer(), nullable=True),
        sa.Column("goals_away", sa.Integer(), nullable=True),
        sa.Column("score_halftime_home", sa.Integer(), nullable=True),
        sa.Column("score_halftime_away", sa.Integer(), nullable=True),
        sa.Column("score_fulltime_home", sa.Integer(), nullable=True),
        sa.Column("score_fulltime_away", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "season BETWEEN 1900 AND 2100",
            name="ck_api_football_matches_season",
        ),
        sa.CheckConstraint(
            "home_team_provider_id <> away_team_provider_id",
            name="ck_api_football_matches_distinct_teams",
        ),
    )
    op.create_table(
        "api_football_standings",
        uuid_pk(),
        *observation_columns("api_football_standings"),
        sa.Column("provider_competition_id", sa.BigInteger(), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("provider_team_id", sa.BigInteger(), nullable=False),
        sa.Column("team_name", sa.String(length=240), nullable=False),
        sa.Column("group_name", sa.String(length=160), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=True),
        sa.Column("goals_diff", sa.Integer(), nullable=True),
        sa.Column("form", sa.String(length=80), nullable=True),
        sa.Column("description", sa.String(length=240), nullable=True),
        sa.Column("played", sa.Integer(), nullable=True),
        sa.Column("wins", sa.Integer(), nullable=True),
        sa.Column("draws", sa.Integer(), nullable=True),
        sa.Column("losses", sa.Integer(), nullable=True),
        sa.Column("goals_for", sa.Integer(), nullable=True),
        sa.Column("goals_against", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "rank >= 1",
            name="ck_api_football_standings_rank_positive",
        ),
    )
    op.create_table(
        "api_football_match_statistics",
        uuid_pk(),
        *observation_columns("api_football_match_statistics"),
        sa.Column("provider_match_id", sa.BigInteger(), nullable=False),
        sa.Column("provider_team_id", sa.BigInteger(), nullable=False),
        sa.Column("statistic_type", sa.String(length=160), nullable=False),
        jsonb("statistic_value", default="", nullable=True),
    )
    op.create_table(
        "api_football_match_events",
        uuid_pk(),
        *observation_columns("api_football_match_events"),
        sa.Column("provider_match_id", sa.BigInteger(), nullable=False),
        sa.Column("event_key", sa.String(length=64), nullable=False),
        sa.Column("elapsed", sa.Integer(), nullable=True),
        sa.Column("extra", sa.Integer(), nullable=True),
        sa.Column("provider_team_id", sa.BigInteger(), nullable=True),
        sa.Column("team_name", sa.String(length=240), nullable=True),
        sa.Column("provider_player_id", sa.BigInteger(), nullable=True),
        sa.Column("player_name", sa.String(length=240), nullable=True),
        sa.Column("provider_assist_id", sa.BigInteger(), nullable=True),
        sa.Column("assist_name", sa.String(length=240), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("detail", sa.String(length=160), nullable=True),
        sa.Column("comments", sa.String(length=500), nullable=True),
    )
    op.create_table(
        "api_football_injuries",
        uuid_pk(),
        *observation_columns("api_football_injuries"),
        sa.Column("provider_match_id", sa.BigInteger(), nullable=True),
        sa.Column("provider_competition_id", sa.BigInteger(), nullable=True),
        sa.Column("season", sa.Integer(), nullable=True),
        sa.Column("provider_team_id", sa.BigInteger(), nullable=False),
        sa.Column("team_name", sa.String(length=240), nullable=False),
        sa.Column("provider_player_id", sa.BigInteger(), nullable=False),
        sa.Column("player_name", sa.String(length=240), nullable=False),
        sa.Column("injury_type", sa.String(length=120), nullable=True),
        sa.Column("reason", sa.String(length=240), nullable=True),
    )
    op.create_table(
        "api_football_lineups",
        uuid_pk(),
        *observation_columns("api_football_lineups"),
        sa.Column("provider_match_id", sa.BigInteger(), nullable=False),
        sa.Column("provider_team_id", sa.BigInteger(), nullable=False),
        sa.Column("team_name", sa.String(length=240), nullable=False),
        sa.Column("formation", sa.String(length=40), nullable=True),
        sa.Column("provider_coach_id", sa.BigInteger(), nullable=True),
        sa.Column("coach_name", sa.String(length=240), nullable=True),
        sa.Column("provider_player_id", sa.BigInteger(), nullable=True),
        sa.Column("player_name", sa.String(length=240), nullable=True),
        sa.Column("number", sa.Integer(), nullable=True),
        sa.Column("position", sa.String(length=20), nullable=True),
        sa.Column("grid", sa.String(length=20), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.CheckConstraint(
            "role IN ('start_xi', 'substitute')",
            name="ck_api_football_lineups_role",
        ),
    )

    indexes = (
        ("ix_sports_sync_runs_provider_started", "sports_sync_runs", ["provider", "started_at"]),
        ("ix_sports_sync_runs_status", "sports_sync_runs", ["status"]),
        ("ix_sports_sync_errors_run", "sports_sync_errors", ["sync_run_id"]),
        (
            "ix_api_football_competitions_provider_id",
            "api_football_competitions",
            ["provider_competition_id"],
        ),
        (
            "ix_api_football_seasons_competition_year",
            "api_football_seasons",
            ["provider_competition_id", "year"],
        ),
        ("ix_api_football_teams_provider_id", "api_football_teams", ["provider_team_id"]),
        ("ix_api_football_matches_provider_id", "api_football_matches", ["provider_match_id"]),
        ("ix_api_football_matches_kickoff", "api_football_matches", ["kickoff_at"]),
        (
            "ix_api_football_matches_competition_season",
            "api_football_matches",
            ["provider_competition_id", "season"],
        ),
        (
            "ix_api_football_standings_scope",
            "api_football_standings",
            ["provider_competition_id", "season"],
        ),
        (
            "ix_api_football_match_statistics_match",
            "api_football_match_statistics",
            ["provider_match_id"],
        ),
        (
            "ix_api_football_match_events_match",
            "api_football_match_events",
            ["provider_match_id"],
        ),
        ("ix_api_football_injuries_match", "api_football_injuries", ["provider_match_id"]),
        ("ix_api_football_lineups_match", "api_football_lineups", ["provider_match_id"]),
    )
    for index_name, table_name, columns in indexes:
        op.create_index(index_name, table_name, columns)

    for table_name in APPEND_ONLY_TABLES:
        trigger_name = f"trg_{table_name}_append_only"
        op.execute(
            f"""
            CREATE TRIGGER {trigger_name}
            BEFORE UPDATE OR DELETE ON {table_name}
            FOR EACH ROW
            EXECUTE FUNCTION prevent_append_only_mutation()
            """
        )

    for table_name in (*EXISTING_PUBLIC_TABLES, *NEW_TABLES):
        op.execute(f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY')
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                    REVOKE ALL ON TABLE "{table_name}" FROM anon;
                END IF;
                IF EXISTS (
                    SELECT 1 FROM pg_roles WHERE rolname = 'authenticated'
                ) THEN
                    REVOKE ALL ON TABLE "{table_name}" FROM authenticated;
                END IF;
            END
            $$
            """
        )


def downgrade() -> None:
    for table_name in reversed(APPEND_ONLY_TABLES):
        op.execute(
            f"DROP TRIGGER IF EXISTS trg_{table_name}_append_only ON {table_name}"
        )
    for table_name in reversed(NEW_TABLES):
        op.drop_table(table_name)
