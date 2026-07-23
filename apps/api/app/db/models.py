import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.naming import conv

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
    sa.CheckConstraint("currency = 'CDF'", name=conv("ck_app_users_currency_cdf")),
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
    sa.CheckConstraint("currency = 'CDF'", name=conv("ck_bankrolls_currency_cdf")),
    sa.CheckConstraint("virtual_balance >= 0", name=conv("ck_bankrolls_virtual_balance_non_negative")),
    sa.CheckConstraint("real_betting_enabled = false", name=conv("ck_bankrolls_real_betting_disabled")),
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
    sa.CheckConstraint("currency = 'CDF'", name=conv("ck_bet_center_budgets_currency_cdf")),
    sa.CheckConstraint("amount >= 0", name=conv("ck_bet_center_budgets_amount_non_negative")),
    sa.CheckConstraint(
        "period_end IS NULL OR period_start IS NULL OR period_end >= period_start",
        name=conv("ck_bet_center_budgets_period_order"),
    ),
    sa.CheckConstraint("real_betting_enabled = false", name=conv("ck_bet_center_budgets_real_betting_disabled")),
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
    sa.CheckConstraint("production_mock_fallback = false", name=conv("ck_providers_no_production_mock_fallback")),
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
    sa.CheckConstraint("currency = 'CDF'", name=conv("ck_tickets_currency_cdf")),
    sa.CheckConstraint("is_real_bet = false", name=conv("ck_tickets_not_real_bet")),
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
    sa.CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name=conv("ck_entity_mappings_validity_order")),
    sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name=conv("ck_entity_mappings_confidence_range")),
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

api_football_fixture_staging = sa.Table(
    "api_football_fixture_staging",
    metadata,
    uuid_pk(),
    sa.Column("provider", sa.String(length=80), nullable=False),
    sa.Column("provider_fixture_id", sa.BigInteger(), nullable=False),
    sa.Column("provider_league_id", sa.BigInteger(), nullable=True),
    sa.Column("provider_season", sa.Integer(), nullable=True),
    sa.Column("fixture_date", sa.DateTime(timezone=True), nullable=True),
    sa.Column("fixture_timezone", sa.String(length=80), nullable=True),
    sa.Column("fixture_status_short", sa.String(length=40), nullable=True),
    sa.Column("fixture_status_long", sa.String(length=120), nullable=True),
    sa.Column("home_team_provider_id", sa.BigInteger(), nullable=True),
    sa.Column("home_team_name", sa.String(length=240), nullable=True),
    sa.Column("away_team_provider_id", sa.BigInteger(), nullable=True),
    sa.Column("away_team_name", sa.String(length=240), nullable=True),
    sa.Column("goals_home", sa.Integer(), nullable=True),
    sa.Column("goals_away", sa.Integer(), nullable=True),
    sa.Column("score_halftime_home", sa.Integer(), nullable=True),
    sa.Column("score_halftime_away", sa.Integer(), nullable=True),
    sa.Column("score_fulltime_home", sa.Integer(), nullable=True),
    sa.Column("score_fulltime_away", sa.Integer(), nullable=True),
    sa.Column("payload_hash", sa.String(length=128), nullable=False),
    jsonb_col("payload_top_level_keys", default="'[]'::jsonb"),
    sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("source_mode", sa.String(length=80), nullable=False),
    created_at(),
    updated_at(),
    sa.UniqueConstraint(
        "provider",
        "provider_fixture_id",
        name="uq_api_football_fixture_staging_provider_fixture",
    ),
)


sports_sync_runs = sa.Table(
    "sports_sync_runs",
    metadata,
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
    jsonb_col("scope"),
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
    jsonb_col("checkpoint"),
    sa.Column("public_error_code", sa.String(length=80), nullable=True),
    created_at(),
    updated_at(),
    sa.CheckConstraint(
        "status IN ('RUNNING', 'SUCCEEDED', 'PARTIAL', 'FAILED')",
        name=conv("ck_sports_sync_runs_status"),
    ),
    sa.CheckConstraint(
        "request_count >= 0 AND records_received >= 0 AND records_inserted >= 0 "
        "AND records_duplicate >= 0 AND records_rejected >= 0",
        name=conv("ck_sports_sync_runs_counters_non_negative"),
    ),
)

sports_sync_errors = sa.Table(
    "sports_sync_errors",
    metadata,
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
    sa.Column("retryable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
    sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    jsonb_col("context"),
    created_at(),
    sa.CheckConstraint("attempt >= 1", name=conv("ck_sports_sync_errors_attempt_positive")),
)


def sports_observation_columns(table_name: str) -> list[sa.SchemaItem]:
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
        jsonb_col("quality_flags", default="'[]'::jsonb"),
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
            name=conv(f"ck_{table_name}_temporal_order"),
        ),
        sa.CheckConstraint(
            "freshness_status IN ('fresh', 'stale', 'unknown')",
            name=conv(f"ck_{table_name}_freshness_status"),
        ),
    ]


api_football_competitions = sa.Table(
    "api_football_competitions",
    metadata,
    uuid_pk(),
    *sports_observation_columns("api_football_competitions"),
    sa.Column("provider_competition_id", sa.BigInteger(), nullable=False),
    sa.Column("name", sa.String(length=240), nullable=False),
    sa.Column("kind", sa.String(length=80), nullable=True),
    sa.Column("country_name", sa.String(length=160), nullable=True),
    sa.Column("country_code", sa.String(length=8), nullable=True),
    sa.Column("current_season", sa.Integer(), nullable=True),
    jsonb_col("coverage"),
    sa.UniqueConstraint(
        "provider",
        "provider_event_id",
        "raw_hash",
        name="uq_api_football_competitions_observation",
    ),
)

api_football_seasons = sa.Table(
    "api_football_seasons",
    metadata,
    uuid_pk(),
    *sports_observation_columns("api_football_seasons"),
    sa.Column("provider_competition_id", sa.BigInteger(), nullable=False),
    sa.Column("year", sa.Integer(), nullable=False),
    sa.Column("starts_on", sa.Date(), nullable=True),
    sa.Column("ends_on", sa.Date(), nullable=True),
    sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    jsonb_col("coverage"),
    sa.CheckConstraint(
        "year BETWEEN 1900 AND 2100",
        name=conv("ck_api_football_seasons_year"),
    ),
    sa.CheckConstraint(
        "ends_on IS NULL OR starts_on IS NULL OR ends_on >= starts_on",
        name=conv("ck_api_football_seasons_date_order"),
    ),
    sa.UniqueConstraint(
        "provider",
        "provider_event_id",
        "raw_hash",
        name="uq_api_football_seasons_observation",
    ),
)

api_football_teams = sa.Table(
    "api_football_teams",
    metadata,
    uuid_pk(),
    *sports_observation_columns("api_football_teams"),
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
    sa.UniqueConstraint(
        "provider",
        "provider_event_id",
        "raw_hash",
        name="uq_api_football_teams_observation",
    ),
)

api_football_matches = sa.Table(
    "api_football_matches",
    metadata,
    uuid_pk(),
    *sports_observation_columns("api_football_matches"),
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
        name=conv("ck_api_football_matches_season"),
    ),
    sa.CheckConstraint(
        "home_team_provider_id <> away_team_provider_id",
        name=conv("ck_api_football_matches_distinct_teams"),
    ),
    sa.UniqueConstraint(
        "provider",
        "provider_event_id",
        "raw_hash",
        name="uq_api_football_matches_observation",
    ),
)

api_football_standings = sa.Table(
    "api_football_standings",
    metadata,
    uuid_pk(),
    *sports_observation_columns("api_football_standings"),
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
    sa.CheckConstraint("rank >= 1", name=conv("ck_api_football_standings_rank_positive")),
    sa.UniqueConstraint(
        "provider",
        "provider_event_id",
        "raw_hash",
        name="uq_api_football_standings_observation",
    ),
)

api_football_match_statistics = sa.Table(
    "api_football_match_statistics",
    metadata,
    uuid_pk(),
    *sports_observation_columns("api_football_match_statistics"),
    sa.Column("provider_match_id", sa.BigInteger(), nullable=False),
    sa.Column("provider_team_id", sa.BigInteger(), nullable=False),
    sa.Column("statistic_type", sa.String(length=160), nullable=False),
    sa.Column(
        "statistic_value",
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    ),
    sa.UniqueConstraint(
        "provider",
        "provider_event_id",
        "raw_hash",
        name="uq_api_football_match_statistics_observation",
    ),
)

api_football_match_events = sa.Table(
    "api_football_match_events",
    metadata,
    uuid_pk(),
    *sports_observation_columns("api_football_match_events"),
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
    sa.UniqueConstraint(
        "provider",
        "provider_event_id",
        "raw_hash",
        name="uq_api_football_match_events_observation",
    ),
)

api_football_injuries = sa.Table(
    "api_football_injuries",
    metadata,
    uuid_pk(),
    *sports_observation_columns("api_football_injuries"),
    sa.Column("provider_match_id", sa.BigInteger(), nullable=True),
    sa.Column("provider_competition_id", sa.BigInteger(), nullable=True),
    sa.Column("season", sa.Integer(), nullable=True),
    sa.Column("provider_team_id", sa.BigInteger(), nullable=False),
    sa.Column("team_name", sa.String(length=240), nullable=False),
    sa.Column("provider_player_id", sa.BigInteger(), nullable=False),
    sa.Column("player_name", sa.String(length=240), nullable=False),
    sa.Column("injury_type", sa.String(length=120), nullable=True),
    sa.Column("reason", sa.String(length=240), nullable=True),
    sa.UniqueConstraint(
        "provider",
        "provider_event_id",
        "raw_hash",
        name="uq_api_football_injuries_observation",
    ),
)

api_football_lineups = sa.Table(
    "api_football_lineups",
    metadata,
    uuid_pk(),
    *sports_observation_columns("api_football_lineups"),
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
        name=conv("ck_api_football_lineups_role"),
    ),
    sa.UniqueConstraint(
        "provider",
        "provider_event_id",
        "raw_hash",
        name="uq_api_football_lineups_observation",
    ),
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
    sa.CheckConstraint(
        "observed_at <= available_at AND available_at <= fetched_at",
        name=conv("ck_provider_observations_temporal_order"),
    ),
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
    sa.CheckConstraint("max_available_at <= as_of", name=conv("ck_feature_snapshots_available_as_of")),
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
    sa.CheckConstraint(
        "decision IN ('ADVICE', 'WATCH', 'NO_BET', 'INSUFFICIENT_DATA', 'SUSPENDED')",
        name=conv("ck_predictions_decision"),
    ),
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
    sa.CheckConstraint("version_number >= 1", name=conv("ck_prediction_versions_version_positive")),
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
    sa.CheckConstraint("odds_decimal IS NULL OR odds_decimal > 1", name=conv("ck_ticket_selections_odds_decimal")),
    sa.CheckConstraint(
        "stake_suggestion_min IS NULL OR stake_suggestion_min >= 0",
        name=conv("ck_ticket_selections_stake_min_non_negative"),
    ),
    sa.CheckConstraint(
        "stake_suggestion_max IS NULL OR stake_suggestion_max >= 0",
        name=conv("ck_ticket_selections_stake_max_non_negative"),
    ),
    sa.CheckConstraint(
        "stake_suggestion_min IS NULL OR stake_suggestion_max IS NULL OR stake_suggestion_max >= stake_suggestion_min",
        name=conv("ck_ticket_selections_stake_order"),
    ),
    sa.CheckConstraint(
        "decision IN ('ADVICE', 'WATCH', 'NO_BET', 'INSUFFICIENT_DATA', 'SUSPENDED')",
        name=conv("ck_ticket_selections_decision"),
    ),
    sa.CheckConstraint("real_betting_enabled = false", name=conv("ck_ticket_selections_real_betting_disabled")),
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
    sa.CheckConstraint(
        "observed_at <= available_at AND available_at <= fetched_at",
        name=conv("ck_post_match_outcomes_temporal_order"),
    ),
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
    sa.CheckConstraint("resolved_at IS NULL OR resolved_at >= opened_at", name=conv("ck_incidents_resolved_after_opened")),
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
    "ix_api_football_fixture_staging_provider_fixture_id",
    api_football_fixture_staging.c.provider_fixture_id,
)
sa.Index(
    "ix_api_football_fixture_staging_fixture_date",
    api_football_fixture_staging.c.fixture_date,
)
sa.Index(
    "ix_api_football_fixture_staging_league_season",
    api_football_fixture_staging.c.provider_league_id,
    api_football_fixture_staging.c.provider_season,
)
sa.Index(
    "ix_api_football_fixture_staging_status_short",
    api_football_fixture_staging.c.fixture_status_short,
)
sa.Index("ix_sports_sync_runs_provider_started", sports_sync_runs.c.provider, sports_sync_runs.c.started_at)
sa.Index("ix_sports_sync_runs_status", sports_sync_runs.c.status)
sa.Index("ix_sports_sync_errors_run", sports_sync_errors.c.sync_run_id)
sa.Index(
    "ix_api_football_competitions_provider_id",
    api_football_competitions.c.provider_competition_id,
)
sa.Index(
    "ix_api_football_seasons_competition_year",
    api_football_seasons.c.provider_competition_id,
    api_football_seasons.c.year,
)
sa.Index("ix_api_football_teams_provider_id", api_football_teams.c.provider_team_id)
sa.Index("ix_api_football_matches_provider_id", api_football_matches.c.provider_match_id)
sa.Index("ix_api_football_matches_kickoff", api_football_matches.c.kickoff_at)
sa.Index(
    "ix_api_football_matches_competition_season",
    api_football_matches.c.provider_competition_id,
    api_football_matches.c.season,
)
sa.Index(
    "ix_api_football_standings_scope",
    api_football_standings.c.provider_competition_id,
    api_football_standings.c.season,
)
sa.Index(
    "ix_api_football_match_statistics_match",
    api_football_match_statistics.c.provider_match_id,
)
sa.Index(
    "ix_api_football_match_events_match",
    api_football_match_events.c.provider_match_id,
)
sa.Index(
    "ix_api_football_injuries_match",
    api_football_injuries.c.provider_match_id,
)
sa.Index(
    "ix_api_football_lineups_match",
    api_football_lineups.c.provider_match_id,
)
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
