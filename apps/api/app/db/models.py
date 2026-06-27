import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

metadata = sa.MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
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


app_users = sa.Table(
    "app_users",
    metadata,
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
    sa.CheckConstraint("currency = 'CDF'", name="app_users_currency_cdf"),
    sa.UniqueConstraint("external_subject", name="uq_app_users_external_subject"),
    sa.UniqueConstraint("email", name="uq_app_users_email"),
)

bankrolls = sa.Table(
    "bankrolls",
    metadata,
    uuid_pk(),
    sa.Column("app_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_users.id"), nullable=False),
    sa.Column("label", sa.String(length=120), nullable=False),
    sa.Column("currency", sa.String(length=3), nullable=False, server_default="CDF"),
    sa.Column("virtual_balance", sa.Numeric(18, 2), nullable=False, server_default="0"),
    sa.Column("real_betting_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    created_at(),
    updated_at(),
    deleted_at(),
    sa.CheckConstraint("currency = 'CDF'", name="bankrolls_currency_cdf"),
    sa.CheckConstraint("virtual_balance >= 0", name="bankrolls_virtual_balance_non_negative"),
    sa.CheckConstraint("real_betting_enabled = false", name="bankrolls_real_betting_disabled"),
)

bet_center_budgets = sa.Table(
    "bet_center_budgets",
    metadata,
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
    sa.CheckConstraint("currency = 'CDF'", name="bet_center_budgets_currency_cdf"),
    sa.CheckConstraint("amount >= 0", name="bet_center_budgets_amount_non_negative"),
    sa.CheckConstraint("period_end IS NULL OR period_start IS NULL OR period_end >= period_start", name="bet_center_budgets_period_order"),
    sa.CheckConstraint("real_betting_enabled = false", name="bet_center_budgets_real_betting_disabled"),
)

providers = sa.Table(
    "providers",
    metadata,
    uuid_pk(),
    sa.Column("provider_key", sa.String(length=80), nullable=False),
    sa.Column("name", sa.String(length=160), nullable=False),
    sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    sa.Column("production_mock_fallback", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    jsonb_col("metadata"),
    created_at(),
    updated_at(),
    sa.CheckConstraint("production_mock_fallback = false", name="providers_no_production_mock_fallback"),
    sa.UniqueConstraint("provider_key", name="uq_providers_provider_key"),
)

provider_capabilities = sa.Table(
    "provider_capabilities",
    metadata,
    uuid_pk(),
    sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("providers.id"), nullable=False),
    sa.Column("capability", sa.String(length=80), nullable=False),
    sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    created_at(),
    sa.UniqueConstraint("provider_id", "capability", name="uq_provider_capabilities_provider_capability"),
)

canonical_entities = sa.Table(
    "canonical_entities",
    metadata,
    uuid_pk(),
    sa.Column("entity_type", sa.String(length=40), nullable=False),
    sa.Column("canonical_key", sa.String(length=160), nullable=False),
    sa.Column("display_name", sa.String(length=240), nullable=False),
    sa.Column("country_code", sa.String(length=3), nullable=True),
    jsonb_col("metadata"),
    created_at(),
    sa.UniqueConstraint("entity_type", "canonical_key", name="uq_canonical_entities_type_key"),
)

fixtures = sa.Table(
    "fixtures",
    metadata,
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

tickets = sa.Table(
    "tickets",
    metadata,
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
    sa.CheckConstraint("currency = 'CDF'", name="tickets_currency_cdf"),
    sa.CheckConstraint("is_real_bet = false", name="tickets_not_real_bet"),
)

entity_mappings = sa.Table(
    "entity_mappings",
    metadata,
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
    sa.CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="entity_mappings_validity_order"),
    sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="entity_mappings_confidence_range"),
    sa.UniqueConstraint("provider_id", "provider_entity_type", "provider_entity_id", "valid_from", name="uq_entity_mappings_provider_entity_valid_from"),
)

raw_payload_refs = sa.Table(
    "raw_payload_refs",
    metadata,
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

provider_observations = sa.Table(
    "provider_observations",
    metadata,
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
    sa.CheckConstraint("observed_at <= available_at AND available_at <= fetched_at", name="provider_observations_temporal_order"),
)

feature_snapshots = sa.Table(
    "feature_snapshots",
    metadata,
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
    sa.CheckConstraint("max_available_at <= as_of", name="feature_snapshots_available_as_of"),
    sa.UniqueConstraint("feature_hash", name="uq_feature_snapshots_feature_hash"),
    sa.UniqueConstraint("immutable_hash", name="uq_feature_snapshots_immutable_hash"),
)

predictions = sa.Table(
    "predictions",
    metadata,
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
    sa.CheckConstraint("decision IN ('ADVICE', 'WATCH', 'NO_BET', 'INSUFFICIENT_DATA', 'SUSPENDED')", name="predictions_decision"),
    sa.UniqueConstraint("prediction_id", name="uq_predictions_prediction_id"),
    sa.UniqueConstraint("immutable_hash", name="uq_predictions_immutable_hash"),
)

prediction_versions = sa.Table(
    "prediction_versions",
    metadata,
    uuid_pk(),
    sa.Column("prediction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("predictions.id"), nullable=False),
    sa.Column("version_number", sa.Integer(), nullable=False),
    jsonb_col("prediction_payload"),
    sa.Column("immutable_hash", sa.String(length=128), nullable=False),
    created_at(),
    sa.CheckConstraint("version_number >= 1", name="prediction_versions_version_positive"),
    sa.UniqueConstraint("prediction_id", "version_number", name="uq_prediction_versions_prediction_version"),
    sa.UniqueConstraint("immutable_hash", name="uq_prediction_versions_immutable_hash"),
)

ticket_selections = sa.Table(
    "ticket_selections",
    metadata,
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
    sa.CheckConstraint("odds_decimal IS NULL OR odds_decimal > 1", name="ticket_selections_odds_decimal"),
    sa.CheckConstraint("stake_suggestion_min IS NULL OR stake_suggestion_min >= 0", name="ticket_selections_stake_min_non_negative"),
    sa.CheckConstraint("stake_suggestion_max IS NULL OR stake_suggestion_max >= 0", name="ticket_selections_stake_max_non_negative"),
    sa.CheckConstraint("stake_suggestion_min IS NULL OR stake_suggestion_max IS NULL OR stake_suggestion_max >= stake_suggestion_min", name="ticket_selections_stake_order"),
    sa.CheckConstraint("decision IN ('ADVICE', 'WATCH', 'NO_BET', 'INSUFFICIENT_DATA', 'SUSPENDED')", name="ticket_selections_decision"),
    sa.CheckConstraint("real_betting_enabled = false", name="ticket_selections_real_betting_disabled"),
)

post_match_outcomes = sa.Table(
    "post_match_outcomes",
    metadata,
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
    sa.CheckConstraint("observed_at <= available_at AND available_at <= fetched_at", name="post_match_outcomes_temporal_order"),
)

audit_logs = sa.Table(
    "audit_logs",
    metadata,
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

incidents = sa.Table(
    "incidents",
    metadata,
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
    sa.CheckConstraint("resolved_at IS NULL OR resolved_at >= opened_at", name="incidents_resolved_after_opened"),
)

sa.Index("ix_bankrolls_app_user_id", bankrolls.c.app_user_id)
sa.Index("ix_bet_center_budgets_app_user_id", bet_center_budgets.c.app_user_id)
sa.Index("ix_tickets_app_user_id", tickets.c.app_user_id)
sa.Index("ix_ticket_selections_ticket_id", ticket_selections.c.ticket_id)
sa.Index("ix_ticket_selections_fixture_id", ticket_selections.c.fixture_id)
sa.Index("ix_provider_capabilities_provider_id", provider_capabilities.c.provider_id)
sa.Index(
    "ix_provider_observations_provider_event_id",
    provider_observations.c.provider,
    provider_observations.c.provider_event_id,
)
sa.Index("ix_provider_observations_available_at", provider_observations.c.available_at)
sa.Index("ix_provider_observations_fetched_at", provider_observations.c.fetched_at)
sa.Index(
    "ix_raw_payload_refs_provider_event_id",
    raw_payload_refs.c.provider_id,
    raw_payload_refs.c.provider_event_id,
)
sa.Index("ix_raw_payload_refs_fetched_at", raw_payload_refs.c.fetched_at)
sa.Index(
    "ix_entity_mappings_provider_entity",
    entity_mappings.c.provider_id,
    entity_mappings.c.provider_entity_type,
    entity_mappings.c.provider_entity_id,
)
sa.Index("ix_fixtures_scheduled_at", fixtures.c.scheduled_at)
sa.Index("ix_feature_snapshots_fixture_as_of", feature_snapshots.c.fixture_id, feature_snapshots.c.as_of)
sa.Index(
    "ix_predictions_fixture_market_time",
    predictions.c.fixture_id,
    predictions.c.market,
    predictions.c.prediction_time,
)
sa.Index("ix_predictions_prediction_time", predictions.c.prediction_time)
sa.Index("ix_prediction_versions_prediction_id", prediction_versions.c.prediction_id)
sa.Index("ix_post_match_outcomes_fixture_id", post_match_outcomes.c.fixture_id)
sa.Index("ix_post_match_outcomes_available_at", post_match_outcomes.c.available_at)
sa.Index("ix_audit_logs_app_user_id", audit_logs.c.app_user_id)
sa.Index("ix_audit_logs_occurred_at", audit_logs.c.occurred_at)
sa.Index("ix_incidents_status", incidents.c.status)
sa.Index("ix_incidents_opened_at", incidents.c.opened_at)
