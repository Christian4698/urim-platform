"""kairos b2.4 append-only analytical journal

Revision ID: 202607280001
Revises: 26fe26a73d5c
Create Date: 2026-07-28 00:01:00+00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "202607280001"
down_revision: str | Sequence[str] | None = "26fe26a73d5c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = (
    "kairos_analysis_journal",
    "kairos_analysis_resolutions",
)


def _uuid_pk() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def _jsonb(name: str) -> sa.Column:
    return sa.Column(
        name,
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text("'{}'::jsonb"),
    )


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


def upgrade() -> None:
    op.create_table(
        "kairos_analysis_journal",
        _uuid_pk(),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            unique=True,
        ),
        sa.Column("provider_match_id", sa.BigInteger(), nullable=False),
        sa.Column("kickoff_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("analysis_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_version", sa.String(length=120), nullable=False),
        sa.Column("market", sa.String(length=80), nullable=False),
        sa.Column(
            "estimated_probability",
            sa.Numeric(8, 7),
            nullable=False,
        ),
        sa.Column("data_quality_score", sa.Numeric(5, 2), nullable=False),
        sa.Column(
            "technical_confidence_score",
            sa.Numeric(5, 2),
            nullable=False,
        ),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("safety_decision", sa.String(length=40), nullable=False),
        sa.Column(
            "analysis_hash",
            sa.String(length=64),
            nullable=False,
        ),
        _jsonb("analysis_payload"),
        sa.Column(
            "immutable_hash",
            sa.String(length=64),
            nullable=False,
            unique=True,
        ),
        _created_at(),
        sa.CheckConstraint(
            "analysis_time <= created_at AND created_at < kickoff_at",
            name="ck_kairos_analysis_journal_pre_match",
        ),
        sa.CheckConstraint(
            "estimated_probability >= 0 AND estimated_probability <= 1",
            name="ck_kairos_analysis_journal_probability",
        ),
        sa.CheckConstraint(
            "data_quality_score >= 0 AND data_quality_score <= 100 "
            "AND technical_confidence_score >= 0 "
            "AND technical_confidence_score <= 65",
            name="ck_kairos_analysis_journal_score_ranges",
        ),
        sa.CheckConstraint(
            "sample_size >= 0",
            name="ck_kairos_analysis_journal_sample_size",
        ),
        sa.CheckConstraint(
            "market IN ("
            "'FIRST_HALF_MORE_GOALS', 'SECOND_HALF_MORE_GOALS', "
            "'EQUAL_HALF_GOALS', 'FIRST_HALF_OVER_0_5', "
            "'SECOND_HALF_OVER_0_5', 'SECOND_HALF_OVER_1_5', "
            "'HOME_OR_DRAW', 'AWAY_OR_DRAW', 'HOME_OR_AWAY'"
            ")",
            name="ck_kairos_analysis_journal_market",
        ),
        sa.CheckConstraint(
            "analysis_hash ~ '^[0-9a-f]{64}$' "
            "AND immutable_hash ~ '^[0-9a-f]{64}$'",
            name="ck_kairos_analysis_journal_hashes",
        ),
        sa.CheckConstraint(
            "safety_decision = 'ANALYSIS_ALLOWED'",
            name="ck_kairos_analysis_journal_allowed_only",
        ),
    )
    op.create_table(
        "kairos_analysis_resolutions",
        _uuid_pk(),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kairos_analysis_journal.analysis_id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("provider_match_id", sa.BigInteger(), nullable=False),
        sa.Column("market", sa.String(length=80), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column(
            "outcome_available_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column(
            "provider_event_id",
            sa.String(length=240),
            nullable=False,
        ),
        sa.Column("source_version", sa.String(length=80), nullable=False),
        sa.Column("raw_hash", sa.String(length=64), nullable=False),
        _jsonb("outcome_payload"),
        sa.Column(
            "immutable_hash",
            sa.String(length=64),
            nullable=False,
            unique=True,
        ),
        _created_at(),
        sa.CheckConstraint(
            "outcome IN ('SUCCESS', 'FAILURE', 'VOID')",
            name="ck_kairos_analysis_resolutions_outcome",
        ),
        sa.CheckConstraint(
            "outcome_available_at <= resolved_at "
            "AND resolved_at <= created_at",
            name="ck_kairos_analysis_resolutions_temporal_order",
        ),
        sa.CheckConstraint(
            "raw_hash ~ '^[0-9a-f]{64}$' "
            "AND immutable_hash ~ '^[0-9a-f]{64}$'",
            name="ck_kairos_analysis_resolutions_hashes",
        ),
    )
    op.create_index(
        "ix_kairos_analysis_journal_match_time",
        "kairos_analysis_journal",
        ["provider_match_id", "analysis_time"],
    )
    op.create_index(
        "ix_kairos_analysis_journal_market",
        "kairos_analysis_journal",
        ["market"],
    )
    op.create_index(
        "ix_kairos_analysis_resolutions_outcome",
        "kairos_analysis_resolutions",
        ["outcome"],
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_kairos_analysis_resolution_integrity()
        RETURNS trigger AS $$
        DECLARE
            journal_match_id bigint;
            journal_kickoff_at timestamptz;
            journal_market text;
            halftime_home integer;
            halftime_away integer;
            fulltime_home integer;
            fulltime_away integer;
            first_half_goals integer;
            full_match_goals integer;
            expected_outcome text;
        BEGIN
            SELECT provider_match_id, kickoff_at, market
            INTO journal_match_id, journal_kickoff_at, journal_market
            FROM kairos_analysis_journal
            WHERE analysis_id = NEW.analysis_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'analysis journal row does not exist';
            END IF;
            IF NEW.provider_match_id <> journal_match_id
                OR NEW.market <> journal_market THEN
                RAISE EXCEPTION 'resolution identity does not match journal';
            END IF;
            IF NEW.resolved_at <= journal_kickoff_at THEN
                RAISE EXCEPTION 'resolution predates kickoff';
            END IF;
            IF NEW.outcome <> 'VOID'
                AND NEW.outcome_available_at < journal_kickoff_at THEN
                RAISE EXCEPTION 'non-void resolution predates kickoff';
            END IF;
            IF NEW.outcome <> 'VOID' THEN
                IF COALESCE(
                    NEW.outcome_payload ->> 'score_fulltime_home',
                    ''
                ) !~ '^[0-9]+$'
                    OR COALESCE(
                        NEW.outcome_payload ->> 'score_fulltime_away',
                        ''
                    ) !~ '^[0-9]+$' THEN
                    RAISE EXCEPTION
                        'non-void resolution requires valid full-time scores';
                END IF;

                fulltime_home := (
                    NEW.outcome_payload ->> 'score_fulltime_home'
                )::integer;
                fulltime_away := (
                    NEW.outcome_payload ->> 'score_fulltime_away'
                )::integer;
                IF fulltime_home > 100 OR fulltime_away > 100 THEN
                    RAISE EXCEPTION
                        'non-void resolution requires valid full-time scores';
                END IF;

                IF NEW.market = 'HOME_OR_DRAW' THEN
                    expected_outcome := CASE
                        WHEN fulltime_home >= fulltime_away
                        THEN 'SUCCESS'
                        ELSE 'FAILURE'
                    END;
                ELSIF NEW.market = 'AWAY_OR_DRAW' THEN
                    expected_outcome := CASE
                        WHEN fulltime_away >= fulltime_home
                        THEN 'SUCCESS'
                        ELSE 'FAILURE'
                    END;
                ELSIF NEW.market = 'HOME_OR_AWAY' THEN
                    expected_outcome := CASE
                        WHEN fulltime_home <> fulltime_away
                        THEN 'SUCCESS'
                        ELSE 'FAILURE'
                    END;
                ELSE
                    IF COALESCE(
                        NEW.outcome_payload ->> 'score_halftime_home',
                        ''
                    ) !~ '^[0-9]+$'
                        OR COALESCE(
                            NEW.outcome_payload ->> 'score_halftime_away',
                            ''
                        ) !~ '^[0-9]+$' THEN
                        RAISE EXCEPTION
                            'non-void resolution requires valid half-time scores';
                    END IF;

                    halftime_home := (
                        NEW.outcome_payload ->> 'score_halftime_home'
                    )::integer;
                    halftime_away := (
                        NEW.outcome_payload ->> 'score_halftime_away'
                    )::integer;
                    IF halftime_home > 100 OR halftime_away > 100 THEN
                        RAISE EXCEPTION
                            'non-void resolution requires valid half-time scores';
                    END IF;

                    first_half_goals := halftime_home + halftime_away;
                    full_match_goals := fulltime_home + fulltime_away;
                    IF first_half_goals > full_match_goals THEN
                        RAISE EXCEPTION
                            'non-void resolution has incoherent scores';
                    END IF;

                    expected_outcome := CASE NEW.market
                        WHEN 'FIRST_HALF_MORE_GOALS' THEN
                            CASE
                                WHEN first_half_goals >
                                    full_match_goals - first_half_goals
                                THEN 'SUCCESS'
                                ELSE 'FAILURE'
                            END
                        WHEN 'SECOND_HALF_MORE_GOALS' THEN
                            CASE
                                WHEN full_match_goals - first_half_goals >
                                    first_half_goals
                                THEN 'SUCCESS'
                                ELSE 'FAILURE'
                            END
                        WHEN 'EQUAL_HALF_GOALS' THEN
                            CASE
                                WHEN first_half_goals =
                                    full_match_goals - first_half_goals
                                THEN 'SUCCESS'
                                ELSE 'FAILURE'
                            END
                        WHEN 'FIRST_HALF_OVER_0_5' THEN
                            CASE
                                WHEN first_half_goals >= 1
                                THEN 'SUCCESS'
                                ELSE 'FAILURE'
                            END
                        WHEN 'SECOND_HALF_OVER_0_5' THEN
                            CASE
                                WHEN full_match_goals - first_half_goals >= 1
                                THEN 'SUCCESS'
                                ELSE 'FAILURE'
                            END
                        WHEN 'SECOND_HALF_OVER_1_5' THEN
                            CASE
                                WHEN full_match_goals - first_half_goals >= 2
                                THEN 'SUCCESS'
                                ELSE 'FAILURE'
                            END
                    END;
                END IF;

                IF expected_outcome IS NULL
                    OR NEW.outcome <> expected_outcome THEN
                    RAISE EXCEPTION
                        'non-void resolution outcome is incoherent';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_kairos_analysis_resolutions_integrity
        BEFORE INSERT ON kairos_analysis_resolutions
        FOR EACH ROW
        EXECUTE FUNCTION enforce_kairos_analysis_resolution_integrity()
        """
    )

    for table_name in TABLES:
        op.execute(
            f"""
            CREATE TRIGGER trg_{table_name}_append_only
            BEFORE UPDATE OR DELETE ON {table_name}
            FOR EACH ROW
            EXECUTE FUNCTION prevent_append_only_mutation()
            """
        )
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
    for table_name in reversed(TABLES):
        op.execute(
            f"DROP TRIGGER IF EXISTS trg_{table_name}_append_only "
            f"ON {table_name}"
        )
        op.drop_table(table_name)
    op.execute(
        "DROP FUNCTION IF EXISTS "
        "enforce_kairos_analysis_resolution_integrity()"
    )
