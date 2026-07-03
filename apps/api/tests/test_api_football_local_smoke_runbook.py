from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.modules.providers.api_football_smoke_client import API_FOOTBALL_SMOKE_ENV_NAMES

client = TestClient(app)

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNBOOK_PATH = REPO_ROOT / "docs" / "39_API_FOOTBALL_LOCAL_SMOKE_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs" / "21_API_AND_DATABASE_SPEC.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"


def test_api_football_local_smoke_runbook_exists_and_covers_safety_checklists() -> None:
    runbook_text = RUNBOOK_PATH.read_text(encoding="utf-8")

    required_fragments = (
        "local-only",
        "jamais etre lance depuis une route FastAPI",
        "hors Git",
        "jamais etre collee dans un prompt",
        ".env.example",
        "environnement local",
        "environnement production doit refuser",
        "Aucune donnee API-Football ne doit etre ecrite en DB",
        "Aucune prediction ne doit etre creee",
        "Aucun bookmaker, betting ou stake",
        "public-safe",
        "Checklist avant execution",
        "`git status` est clean",
        "branche courante est une branche dediee",
        "Docker et DB ne sont pas necessaires",
        "mode smoke est explicitement active",
        "mode read-only est explicitement confirme",
        "absence de write DB est confirmee",
        "absence de creation de prediction est confirmee",
        "absence de betting, bookmaker et stake est confirmee",
        "Checklist apres execution",
        "Supprimer les variables sensibles du terminal",
        "Verifier les logs locaux",
        "Verifier l'absence de payload brut dans le repo",
    )
    for fragment in required_fragments:
        assert fragment in runbook_text


def test_api_football_local_smoke_runbook_does_not_expose_provider_secret_or_url_material() -> None:
    public_docs = "\n".join(
        [
            RUNBOOK_PATH.read_text(encoding="utf-8"),
            SPEC_PATH.read_text(encoding="utf-8"),
            INDEX_PATH.read_text(encoding="utf-8"),
        ]
    ).lower()

    forbidden_fragments = (
        "http://",
        "https://",
        "api-football.com",
        "api-sports",
        "rapidapi",
        "x-rapidapi",
        "demo_non_prod_fake_phase20",
        "provider_api_key",
        "provider_api_secret",
        "provider_client_secret",
    )
    for fragment in forbidden_fragments:
        assert fragment not in public_docs

    for env_name in API_FOOTBALL_SMOKE_ENV_NAMES:
        assert env_name.lower() not in public_docs


def test_api_football_local_smoke_runbook_adds_no_public_smoke_endpoint() -> None:
    for path in (
        "/api/v1/providers/smoke",
        "/api/v1/providers/local-smoke",
        "/api/v1/providers/smoke/runbook",
        "/api/v1/providers/api-football/local-smoke",
    ):
        response = client.get(path)

        assert response.status_code == 404
