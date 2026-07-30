from __future__ import annotations

import argparse
import os
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.db.isolation import (
    isolated_psycopg_url,
    validate_isolated_test_database,
)

API_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = API_ROOT / "alembic.ini"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate B1_TEST_DATABASE_URL and optionally apply migrations "
            "without printing connection values."
        )
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Apply all Alembic migrations after the isolation gate passes.",
    )
    args = parser.parse_args()

    test_database_url = os.environ.get("B1_TEST_DATABASE_URL")
    if "DATABASE_URL" in os.environ:
        print("POSTGRES_GATE_STATUS=REFUSED")
        print("POSTGRES_GATE_REASON=DATABASE_URL_MUST_BE_ABSENT")
        return 2
    result = validate_isolated_test_database(
        test_database_url,
        database_url=None,
        app_env=os.environ.get("APP_ENV"),
    )
    print(f"POSTGRES_GATE_STATUS={'ALLOWED' if result.safe else 'REFUSED'}")
    print(f"POSTGRES_GATE_REASON={result.reason}")
    if not result.safe:
        return 2

    if not args.migrate:
        return 0

    assert test_database_url is not None
    alembic_config = Config(str(ALEMBIC_INI))
    alembic_config.attributes["database_url"] = isolated_psycopg_url(
        test_database_url
    )
    command.upgrade(alembic_config, "head")
    command.upgrade(alembic_config, "head")

    print("POSTGRES_MIGRATIONS=APPLIED_TO_ISOLATED_TEST_DATABASE")
    print("POSTGRES_MIGRATION_IDEMPOTENCE=PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
