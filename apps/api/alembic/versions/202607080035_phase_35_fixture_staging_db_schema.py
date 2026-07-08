"""phase 35 fixture staging db schema

Revision ID: 202607080035
Revises: 202606260001
Create Date: 2026-07-08 00:35:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "202607080035"
down_revision: str | None = "202606260001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


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


def upgrade() -> None:
    op.create_table(
        "api_football_fixture_staging",
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
        sa.Column(
            "payload_top_level_keys",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
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
    op.create_index(
        "ix_api_football_fixture_staging_provider_fixture_id",
        "api_football_fixture_staging",
        ["provider_fixture_id"],
    )
    op.create_index(
        "ix_api_football_fixture_staging_fixture_date",
        "api_football_fixture_staging",
        ["fixture_date"],
    )
    op.create_index(
        "ix_api_football_fixture_staging_league_season",
        "api_football_fixture_staging",
        ["provider_league_id", "provider_season"],
    )
    op.create_index(
        "ix_api_football_fixture_staging_status_short",
        "api_football_fixture_staging",
        ["fixture_status_short"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_api_football_fixture_staging_status_short",
        table_name="api_football_fixture_staging",
    )
    op.drop_index(
        "ix_api_football_fixture_staging_league_season",
        table_name="api_football_fixture_staging",
    )
    op.drop_index(
        "ix_api_football_fixture_staging_fixture_date",
        table_name="api_football_fixture_staging",
    )
    op.drop_index(
        "ix_api_football_fixture_staging_provider_fixture_id",
        table_name="api_football_fixture_staging",
    )
    op.drop_table("api_football_fixture_staging")
