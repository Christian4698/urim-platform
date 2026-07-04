from pathlib import Path
import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.providers.api_football_smoke_client import API_FOOTBALL_SMOKE_ENV_NAMES

client = TestClient(app)

REPO_ROOT = Path(__file__).resolve().parents[3]
PROTOCOL_PATH = REPO_ROOT / "docs" / "41_API_FOOTBALL_FIRST_REAL_LOCAL_SMOKE_PROTOCOL.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "022-phase-22-api-football-first-real-local-smoke-protocol.md"
)
PUBLIC_PHASE_22_DOCS = (
    PROTOCOL_PATH,
    ACTIVE_PLAN_PATH,
    REPO_ROOT / "docs" / "21_API_AND_DATABASE_SPEC.md",
    REPO_ROOT / "docs" / "index.md",
    REPO_ROOT / "apps" / "api" / "README.md",
)


def test_first_real_local_smoke_protocol_exists_and_covers_checklists() -> None:
    protocol_text = PROTOCOL_PATH.read_text(encoding="utf-8")

    required_fragments = (
        "Phase 22",
        "ne lance aucun appel API-Football",
        "jamais etre collee dans ChatGPT, Codex, Claude, Git",
        "terminal local",
        "fichier local non tracke",
        "Aucune route FastAPI",
        "Aucune donnee provider ne doit etre ecrite en DB",
        "Aucune prediction ne doit etre creee",
        "Aucun bookmaker, betting, cote, stake",
        "Tout payload brut provider doit rester hors repo",
        "Checklist pre-smoke",
        "`git status` est clean",
        "branche courante est une branche dediee",
        "`APP_ENV`",
        "mode smoke est explicitement active",
        "mode read-only est confirme",
        "L'absence de write DB est confirmee",
        "L'absence de creation de prediction est confirmee",
        "L'absence de betting, bookmaker et stake est confirmee",
        "endpoint public n'est utilise",
        "Commande future attendue",
        "SET_LOCAL_AUTH_MATERIAL_HERE",
        "SET_LOCAL_PROVIDER_BASE_REFERENCE_HERE",
        "Checklist post-smoke",
        "Supprimer les variables sensibles du terminal",
        "Verifier l'absence de payload brut dans le repo",
        "Verifier l'absence de write DB",
        "Verifier l'absence de prediction",
        "Verifier l'absence de betting",
        "resume hashe et public-safe",
    )
    for fragment in required_fragments:
        assert fragment in protocol_text


def test_first_real_local_smoke_protocol_uses_only_public_safe_placeholders() -> None:
    public_docs = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_PHASE_22_DOCS).lower()

    assert "set_local_auth_material_here" in public_docs
    assert "set_local_provider_base_reference_here" in public_docs
    assert "api_football_smoke_env_names" not in public_docs

    forbidden_fragments = (
        "http://",
        "https://",
        "api-football.com",
        "api-sports",
        "rapidapi",
        "x-rapidapi",
        "demo_non_prod_fake_phase18_auth_material",
        "demo_non_prod_fake_phase19_auth_material",
        "demo_non_prod_fake_phase21_auth_material",
        "bearer ",
        "authorization:",
        "x-rapidapi-key",
        "api_key=",
        "apikey",
    )
    for fragment in forbidden_fragments:
        assert fragment not in public_docs

    real_key_patterns = (
        r"\bsk-[a-z0-9_-]{20,}\b",
        r"\blive_[a-z0-9]{24,}\b",
    )
    for pattern in real_key_patterns:
        assert re.search(pattern, public_docs) is None

    for env_name in API_FOOTBALL_SMOKE_ENV_NAMES:
        assert env_name.lower() not in public_docs


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/providers/smoke",
        "/api/v1/providers/local-smoke",
        "/api/v1/providers/first-real-smoke",
        "/api/v1/providers/protocol",
        "/api/v1/providers/api-football/first-real-smoke",
        "/api/v1/providers/api-football/protocol",
        "/api/v1/providers/api-football/first-real-local-smoke",
    ],
)
def test_first_real_local_smoke_protocol_adds_no_public_endpoint(path: str) -> None:
    response = client.get(path)

    assert response.status_code == 404


def test_first_real_local_smoke_protocol_is_not_imported_by_fastapi() -> None:
    fastapi_sources = [
        *Path("app/api").rglob("*.py"),
        Path("app/main.py"),
    ]

    for source_path in fastapi_sources:
        source = source_path.read_text(encoding="utf-8")
        assert "api_football_local_smoke_harness" not in source
        assert "41_API_FOOTBALL_FIRST_REAL_LOCAL_SMOKE_PROTOCOL" not in source
        assert "first_real_local_smoke_protocol" not in source


def test_first_real_local_smoke_protocol_does_not_touch_db_migrations_or_frontend() -> None:
    guarded_paths = [
        REPO_ROOT / "apps" / "api" / "alembic",
        REPO_ROOT / "apps" / "api" / "app" / "db",
        REPO_ROOT / "apps" / "web",
    ]

    for guarded_path in guarded_paths:
        for source_path in guarded_path.rglob("*"):
            if source_path.is_file():
                source = source_path.read_text(encoding="utf-8", errors="ignore").lower()
                assert "phase-22-api-football-first-real-local-smoke-protocol" not in source
                assert "first real local smoke" not in source
