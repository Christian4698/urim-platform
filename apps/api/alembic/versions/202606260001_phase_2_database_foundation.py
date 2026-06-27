"""phase 2 database foundation

Revision ID: 202606260001
Revises:
Create Date: 2026-06-26 00:01:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "202606260001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APPEND_ONLY_TRIGGERS = {
    "predictions": "trg_predictions_append_only",
    "prediction_versions": "trg_prediction_versions_append_only",
    "feature_snapshots": "trg_feature_snapshots_append_only",
    "provider_observations": "trg_provider_observations_append_only",
    "raw_payload_refs": "trg_raw_payload_refs_append_only",
    "audit_logs": "trg_audit_logs_append_only",
    "post_match_outcomes": "trg_post_match_outcomes_append_only",
}


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


def updated_at() -> sa.Column:
    return sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True)


def deleted_at() -> sa.Column:
    return sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)


def jsonb_col(name: str, nullable: bool = False, default: str = "'{}'::jsonb") -> sa.Column:
    return sa.Column(
        name,
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=nullable,
        server_default=sa.text(default) if default else None,
    )


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "app_users",
        uuid_pk(),
        sa.Column("external_subject", sa.String(length=128), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("display_name", sa.String(length=160), nullable=True),
        sa.Column("locale", sa.String(length=16), nullable=False, server_default="fr-CD"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="CDF"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        created_at(),
        updated_at(),
        deleted_at(),
        sa.CheckConstraint("currency = 'CDF'", name="ck_app_users_currency_cdf"),
        sa.UniqueConstraint("external_subject", name="uq_app_users_external_subject"),
        sa.UniqueConstraint("email", name="uq_app_users_email"),
    )

    op.create_table(
        "bankrolls",
        uuid_pk(),
        sa.Column("app_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_users.id"), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="CDF"),
        sa.Column("virtual_balance", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("real_betting_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        created_at(),
        updated_at(),
        deleted_at(),
        sa.CheckConstraint("currency = 'CDF'", name="ck_bankrolls_currency_cdf"),
        sa.CheckConstraint("virtual_balance >= 0", name="ck_bankrolls_virtual_balance_non_negative"),
        sa.CheckConstraint("real_betting_enabled = false", name="ck_bankrolls_real_betting_disabled"),
    )

    op.create_table(
        "bet_center_budgets",
        uuid_pk(),
        sa.Column("app_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_users.id"), nullable=False),
        sa.Column("bankroll_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bankrolls.id"), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="CDF"),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("real_betting_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        created_at(),
        updated_at(),
        deleted_at(),
        sa.CheckConstraint("currency = 'CDF'", name="ck_bet_center_budgets_currency_cdf"),
        sa.CheckConstraint("amount >= 0", name="ck_bet_center_budgets_amount_non_negative"),
        sa.CheckConstraint("period_end IS NULL OR period_start IS NULL OR period_end >= period_start", name="ck_bet_center_budgets_period_order"),
        sa.CheckConstraint("real_betting_enabled = false", name="ck_bet_center_budgets_real_betting_disabled"),
    )

    op.create_table(
        "providers",
        uuid_pk(),
        sa.Column("provider_key", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("production_mock_fallback", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        jsonb_col("metadata"),
        created_at(),
        updated_at(),
        sa.CheckConstraint("production_mock_fallback = false", name="ck_providers_no_production_mock_fallback"),
        sa.UniqueConstraint("provider_key", name="uq_providers_provider_key"),
    )

    op.create_table(
        "provider_capabilities",
        uuid_pk(),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("capability", sa.String(length=80), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        created_at(),
        sa.UniqueConstraint("provider_id", "capability", name="uq_provider_capabilities_provider_capability"),
    )

    op.create_table(
        "canonical_entities",
        uuid_pk(),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("canonical_key", sa.String(length=160), nullable=False),
        sa.Column("display_name", sa.String(length=240), nullable=False),
        sa.Column("country_code", sa.String(length=3), nullable=True),
        jsonb_col("metadata"),
        created_at(),
        sa.UniqueConstraint("entity_type", "canonical_key", name="uq_canonical_entities_type_key"),
    )

    op.create_table(
        "fixtures",
        uuid_pk(),
        sa.Column("canonical_key", sa.String(length=160), nullable=False),
        sa.Column("home_entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_entities.id"), nullable=True),
        sa.Column("away_entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_entities.id"), nullable=True),
        sa.Column("competition_entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_entities.id"), nullable=True),
        sa.Column("season_label", sa.String(length=40), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="SCHEDULED"),
        jsonb_col("metadata"),
        created_at(),
        sa.UniqueConstraint("canonical_key", name="uq_fixtures_canonical_key"),
    )

    op.create_table(
        "tickets",
        uuid_pk(),
        sa.Column("app_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_users.id"), nullable=False),
        sa.Column("bankroll_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bankrolls.id"), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="CDF"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="DRAFT"),
        sa.Column("is_real_bet", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("user_declared_result", sa.String(length=80), nullable=True),
        sa.Column("user_declared_profit_loss", sa.Numeric(18, 2), nullable=True),
        created_at(),
        updated_at(),
        deleted_at(),
        sa.CheckConstraint("currency = 'CDF'", name="ck_tickets_currency_cdf"),
        sa.CheckConstraint("is_real_bet = false", name="ck_tickets_not_real_bet"),
    )

    op.create_table(
        "entity_mappings",
        uuid_pk(),
        sa.Column("canonical_entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_entities.id"), nullable=False),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("provider_entity_id", sa.String(length=160), nullable=False),
        sa.Column("provider_entity_type", sa.String(length=40), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False, server_default="1"),
        jsonb_col("metadata"),
        created_at(),
        sa.CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="ck_entity_mappings_validity_order"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_entity_mappings_confidence_range"),
        sa.UniqueConstraint("provider_id", "provider_entity_type", "provider_entity_id", "valid_from", name="uq_entity_mappings_provider_entity_valid_from"),
    )

    op.create_table(
        "raw_payload_refs",
        uuid_pk(),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("provider_event_id", sa.String(length=160), nullable=False),
        sa.Column("endpoint", sa.String(length=240), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_version", sa.String(length=80), nullable=False),
        sa.Column("raw_hash", sa.String(length=128), nullable=False),
        sa.Column("storage_uri", sa.Text(), nullable=True),
        jsonb_col("metadata"),
        created_at(),
        sa.UniqueConstraint("raw_hash", name="uq_raw_payload_refs_raw_hash"),
    )

    op.create_table(
        "provider_observations",
        uuid_pk(),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("provider_event_id", sa.String(length=160), nullable=False),
        sa.Column("raw_payload_ref_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("raw_payload_refs.id"), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_version", sa.String(length=80), nullable=False),
        sa.Column("raw_hash", sa.String(length=128), nullable=False),
        jsonb_col("quality_flags", default="'[]'::jsonb"),
        jsonb_col("data"),
        created_at(),
        sa.CheckConstraint("observed_at <= available_at AND available_at <= fetched_at", name="ck_provider_observations_temporal_order"),
    )

    op.create_table(
        "feature_snapshots",
        uuid_pk(),
        sa.Column("fixture_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fixtures.id"), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("feature_hash", sa.String(length=128), nullable=False),
        sa.Column("raw_hash", sa.String(length=128), nullable=False),
        jsonb_col("source_observation_ids", default="'[]'::jsonb"),
        jsonb_col("features"),
        sa.Column("immutable_hash", sa.String(length=128), nullable=False),
        created_at(),
        sa.CheckConstraint("max_available_at <= as_of", name="ck_feature_snapshots_available_as_of"),
        sa.UniqueConstraint("feature_hash", name="uq_feature_snapshots_feature_hash"),
        sa.UniqueConstraint("immutable_hash", name="uq_feature_snapshots_immutable_hash"),
    )

    op.create_table(
        "predictions",
        uuid_pk(),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fixture_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fixtures.id"), nullable=True),
        sa.Column("feature_snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("feature_snapshots.id"), nullable=False),
        sa.Column("model_version", sa.String(length=120), nullable=False),
        sa.Column("prediction_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("market", sa.String(length=80), nullable=False),
        jsonb_col("probabilities"),
        sa.Column("calibration_bucket", sa.String(length=80), nullable=True),
        sa.Column("decision", sa.String(length=40), nullable=False),
        jsonb_col("reasons", default="'[]'::jsonb"),
        jsonb_col("data_freshness"),
        sa.Column("odds_snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("immutable_hash", sa.String(length=128), nullable=False),
        created_at(),
        sa.CheckConstraint("decision IN ('ADVICE', 'WATCH', 'NO_BET', 'INSUFFICIENT_DATA', 'SUSPENDED')", name="ck_predictions_decision"),
        sa.UniqueConstraint("prediction_id", name="uq_predictions_prediction_id"),
        sa.UniqueConstraint("immutable_hash", name="uq_predictions_immutable_hash"),
    )

    op.create_table(
        "prediction_versions",
        uuid_pk(),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("predictions.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        jsonb_col("prediction_payload"),
        sa.Column("immutable_hash", sa.String(length=128), nullable=False),
        created_at(),
        sa.CheckConstraint("version_number >= 1", name="ck_prediction_versions_version_positive"),
        sa.UniqueConstraint("prediction_id", "version_number", name="uq_prediction_versions_prediction_version"),
        sa.UniqueConstraint("immutable_hash", name="uq_prediction_versions_immutable_hash"),
    )

    op.create_table(
        "ticket_selections",
        uuid_pk(),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column("fixture_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fixtures.id"), nullable=True),
        sa.Column("market", sa.String(length=80), nullable=False),
        sa.Column("selection", sa.String(length=160), nullable=False),
        sa.Column("odds_decimal", sa.Numeric(10, 4), nullable=True),
        sa.Column("stake_suggestion_min", sa.Numeric(18, 2), nullable=True),
        sa.Column("stake_suggestion_max", sa.Numeric(18, 2), nullable=True),
        sa.Column("decision", sa.String(length=40), nullable=False, server_default="WATCH"),
        sa.Column("real_betting_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        created_at(),
        updated_at(),
        deleted_at(),
        sa.CheckConstraint("odds_decimal IS NULL OR odds_decimal > 1", name="ck_ticket_selections_odds_decimal"),
        sa.CheckConstraint("stake_suggestion_min IS NULL OR stake_suggestion_min >= 0", name="ck_ticket_selections_stake_min_non_negative"),
        sa.CheckConstraint("stake_suggestion_max IS NULL OR stake_suggestion_max >= 0", name="ck_ticket_selections_stake_max_non_negative"),
        sa.CheckConstraint("stake_suggestion_min IS NULL OR stake_suggestion_max IS NULL OR stake_suggestion_max >= stake_suggestion_min", name="ck_ticket_selections_stake_order"),
        sa.CheckConstraint("decision IN ('ADVICE', 'WATCH', 'NO_BET', 'INSUFFICIENT_DATA', 'SUSPENDED')", name="ck_ticket_selections_decision"),
        sa.CheckConstraint("real_betting_enabled = false", name="ck_ticket_selections_real_betting_disabled"),
    )

    op.create_table(
        "post_match_outcomes",
        uuid_pk(),
        sa.Column("fixture_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fixtures.id"), nullable=True),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("providers.id"), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("provider_event_id", sa.String(length=160), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_version", sa.String(length=80), nullable=False),
        jsonb_col("quality_flags", default="'[]'::jsonb"),
        sa.Column("raw_hash", sa.String(length=128), nullable=False),
        jsonb_col("outcome_payload"),
        created_at(),
        sa.CheckConstraint("observed_at <= available_at AND available_at <= fetched_at", name="ck_post_match_outcomes_temporal_order"),
    )

    op.create_table(
        "audit_logs",
        uuid_pk(),
        sa.Column("app_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_users.id"), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("request_id", sa.String(length=120), nullable=True),
        jsonb_col("metadata"),
        created_at(),
    )

    op.create_table(
        "incidents",
        uuid_pk(),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="OPEN"),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        jsonb_col("metadata"),
        created_at(),
        updated_at(),
        sa.CheckConstraint("resolved_at IS NULL OR resolved_at >= opened_at", name="ck_incidents_resolved_after_opened"),
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_append_only_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'append-only table % cannot be %', TG_TABLE_NAME, TG_OP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_prediction_snapshot_temporal_integrity()
        RETURNS trigger AS $$
        DECLARE
            snapshot_max_available_at timestamptz;
        BEGIN
            SELECT max_available_at INTO snapshot_max_available_at
            FROM feature_snapshots
            WHERE id = NEW.feature_snapshot_id;

            IF snapshot_max_available_at IS NULL THEN
                RAISE EXCEPTION 'feature snapshot % does not exist', NEW.feature_snapshot_id;
            END IF;

            IF snapshot_max_available_at > NEW.prediction_time THEN
                RAISE EXCEPTION 'feature snapshot max_available_at % exceeds prediction_time %',
                    snapshot_max_available_at, NEW.prediction_time;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_predictions_temporal_integrity
        BEFORE INSERT OR UPDATE ON predictions
        FOR EACH ROW
        EXECUTE FUNCTION enforce_prediction_snapshot_temporal_integrity();
        """
    )

    for table_name, trigger_name in APPEND_ONLY_TRIGGERS.items():
        op.execute(
            f"""
            CREATE TRIGGER {trigger_name}
            BEFORE UPDATE OR DELETE ON {table_name}
            FOR EACH ROW
            EXECUTE FUNCTION prevent_append_only_mutation();
            """
        )

    op.create_index("ix_bankrolls_app_user_id", "bankrolls", ["app_user_id"])
    op.create_index("ix_bet_center_budgets_app_user_id", "bet_center_budgets", ["app_user_id"])
    op.create_index("ix_tickets_app_user_id", "tickets", ["app_user_id"])
    op.create_index("ix_ticket_selections_ticket_id", "ticket_selections", ["ticket_id"])
    op.create_index("ix_ticket_selections_fixture_id", "ticket_selections", ["fixture_id"])
    op.create_index("ix_provider_capabilities_provider_id", "provider_capabilities", ["provider_id"])
    op.create_index("ix_provider_observations_provider_event_id", "provider_observations", ["provider", "provider_event_id"])
    op.create_index("ix_provider_observations_available_at", "provider_observations", ["available_at"])
    op.create_index("ix_provider_observations_fetched_at", "provider_observations", ["fetched_at"])
    op.create_index("ix_raw_payload_refs_provider_event_id", "raw_payload_refs", ["provider_id", "provider_event_id"])
    op.create_index("ix_raw_payload_refs_fetched_at", "raw_payload_refs", ["fetched_at"])
    op.create_index("ix_entity_mappings_provider_entity", "entity_mappings", ["provider_id", "provider_entity_type", "provider_entity_id"])
    op.create_index("ix_fixtures_scheduled_at", "fixtures", ["scheduled_at"])
    op.create_index("ix_feature_snapshots_fixture_as_of", "feature_snapshots", ["fixture_id", "as_of"])
    op.create_index("ix_predictions_fixture_market_time", "predictions", ["fixture_id", "market", "prediction_time"])
    op.create_index("ix_predictions_prediction_time", "predictions", ["prediction_time"])
    op.create_index("ix_prediction_versions_prediction_id", "prediction_versions", ["prediction_id"])
    op.create_index("ix_post_match_outcomes_fixture_id", "post_match_outcomes", ["fixture_id"])
    op.create_index("ix_post_match_outcomes_available_at", "post_match_outcomes", ["available_at"])
    op.create_index("ix_audit_logs_app_user_id", "audit_logs", ["app_user_id"])
    op.create_index("ix_audit_logs_occurred_at", "audit_logs", ["occurred_at"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_opened_at", "incidents", ["opened_at"])


def downgrade() -> None:
    for table_name, trigger_name in reversed(APPEND_ONLY_TRIGGERS.items()):
        op.execute(f"DROP TRIGGER IF EXISTS {trigger_name} ON {table_name}")

    op.execute("DROP TRIGGER IF EXISTS trg_predictions_temporal_integrity ON predictions")
    op.execute("DROP FUNCTION IF EXISTS enforce_prediction_snapshot_temporal_integrity()")
    op.execute("DROP FUNCTION IF EXISTS prevent_append_only_mutation()")

    for table_name in (
        "incidents",
        "audit_logs",
        "post_match_outcomes",
        "ticket_selections",
        "prediction_versions",
        "predictions",
        "feature_snapshots",
        "provider_observations",
        "raw_payload_refs",
        "entity_mappings",
        "tickets",
        "fixtures",
        "canonical_entities",
        "provider_capabilities",
        "providers",
        "bet_center_budgets",
        "bankrolls",
        "app_users",
    ):
        op.drop_table(table_name)
