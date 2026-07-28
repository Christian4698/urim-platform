import os
from pathlib import Path
import subprocess
import sys


API_ROOT = Path(__file__).resolve().parents[1]


def test_production_app_env_disables_openapi_swagger_and_redoc_at_runtime() -> None:
    environment = os.environ.copy()
    environment["APP_ENV"] = "production"
    for variable in (
        "API_FOOTBALL_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "PROVIDER_API_KEY",
        "PROVIDER_API_SECRET",
        "PROVIDER_CLIENT_SECRET",
        "PROVIDER_WEBHOOK_SECRET",
    ):
        environment.pop(variable, None)

    code = """
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
print(",".join(str(client.get(path).status_code) for path in (
    "/openapi.json",
    "/docs",
    "/redoc",
)))
""".strip()
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=API_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "404,404,404"
