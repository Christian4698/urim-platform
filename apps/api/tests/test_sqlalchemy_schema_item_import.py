import os
from pathlib import Path
import subprocess
import sys

import sqlalchemy

API_ROOT = Path(__file__).resolve().parents[1]
SQLALCHEMY_SITE_ROOT = Path(sqlalchemy.__file__).resolve().parents[1]
MIGRATION_FILE = (
    API_ROOT
    / "alembic"
    / "versions"
    / "26fe26a73d5c_programme_b1_sports_data_foundation.py"
)


def test_models_and_migration_import_with_resolvable_schema_item_annotation() -> None:
    script = """
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from typing import get_args, get_origin, get_type_hints

sys.path[:0] = [sys.argv[2], sys.argv[3]]

from sqlalchemy.schema import SchemaItem
from app.db import models

models_return = get_type_hints(models.sports_observation_columns)["return"]
assert get_origin(models_return) is list
assert get_args(models_return) == (SchemaItem,)
assert "api_football_matches" in models.metadata.tables

migration_path = Path(sys.argv[1])
spec = spec_from_file_location("programme_b1_migration_import_test", migration_path)
assert spec is not None and spec.loader is not None
migration = module_from_spec(spec)
spec.loader.exec_module(migration)
migration_return = get_type_hints(migration.observation_columns)["return"]
assert get_origin(migration_return) is list
assert get_args(migration_return) == (SchemaItem,)
"""
    environment = os.environ.copy()
    for key in tuple(environment):
        if key == "DATABASE_URL" or key.startswith("API_FOOTBALL_"):
            environment.pop(key)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            script,
            str(MIGRATION_FILE),
            str(API_ROOT),
            str(SQLALCHEMY_SITE_ROOT),
        ],
        cwd=API_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stderr
