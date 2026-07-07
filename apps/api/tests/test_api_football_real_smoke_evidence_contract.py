from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "44_API_FOOTBALL_REAL_SMOKE_EVIDENCE_AND_SAFE_RESPONSE_CONTRACT.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"

PUBLIC_SAFE_HASH = "c4dc669eb135caca91c623ce5b30a6aea065ee70134cee45111a576fe19b59ed"
PUBLIC_SAFE_TOP_LEVEL_KEYS = ("errors", "get", "paging", "parameters", "response", "results")
ALLOWED_SAFE_CONTRACT_FIELDS = (
    "status",
    "executed",
    "provider",
    "mode",
    "payload_hash",
    "payload_top_level_keys",
    "db_writes",
    "prediction_created",
    "betting_created",
)


def _read_phase_25_doc() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _contract_field_lines(doc_text: str) -> list[str]:
    in_contract = False
    fields: list[str] = []

    for line in doc_text.splitlines():
        if line == "## Allowed safe response contract":
            in_contract = True
            continue
        if in_contract and line.startswith("## "):
            break
        match = re.fullmatch(r"- `([a-z_]+)`", line)
        if in_contract and match:
            fields.append(match.group(1))

    return fields


def test_api_football_real_smoke_evidence_doc_exists_and_records_public_safe_result() -> None:
    doc_text = _read_phase_25_doc()

    assert "Phase 25" in doc_text
    assert "status=completed_first_real_local_smoke" in doc_text
    assert "executed=true" in doc_text
    assert "provider=api-football" in doc_text
    assert "mode=first_real_local_smoke_only" in doc_text
    assert f"payload_hash={PUBLIC_SAFE_HASH}" in doc_text
    for key in PUBLIC_SAFE_TOP_LEVEL_KEYS:
        assert key in doc_text
    assert "db_writes=false" in doc_text
    assert "prediction_created=false" in doc_text
    assert "betting_created=false" in doc_text


def test_api_football_real_smoke_evidence_doc_defines_only_allowed_safe_contract_fields() -> None:
    doc_text = _read_phase_25_doc()

    assert tuple(_contract_field_lines(doc_text)) == ALLOWED_SAFE_CONTRACT_FIELDS
    for field in ALLOWED_SAFE_CONTRACT_FIELDS:
        assert field in doc_text


def test_api_football_real_smoke_evidence_doc_has_required_scope_sections() -> None:
    doc_text = _read_phase_25_doc()

    for section in (
        "## What this proves",
        "## What this does NOT prove yet",
        "## Next allowed read-only endpoints",
        "## Forbidden until later phases",
    ):
        assert section in doc_text

    for endpoint_label in (
        "fixtures",
        "standings",
        "team statistics",
        "fixture events",
        "fixture lineups",
        "fixture statistics",
    ):
        assert endpoint_label in doc_text

    assert "Phase 25 enables none of these endpoints" in doc_text
    assert "permits no DB writes" in doc_text


def test_api_football_real_smoke_evidence_index_references_phase_25_doc() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "44_API_FOOTBALL_REAL_SMOKE_EVIDENCE_AND_SAFE_RESPONSE_CONTRACT.md" in index_text


def test_api_football_real_smoke_evidence_doc_does_not_expose_secret_or_provider_material() -> None:
    doc_text = _read_phase_25_doc()
    doc_text_lower = doc_text.lower()

    forbidden_fragments = (
        "http://",
        "https://",
        "api-football.com",
        "api-sports",
        "rapidapi",
        "x-rapidapi",
        "x-apisports-key",
        "x-api-key",
        "authorization:",
        "bearer ",
        "api_key=",
        "apikey",
        "api-key:",
        "credential=",
        "token=",
        "secret=",
        "provider_credentials",
    )
    for fragment in forbidden_fragments:
        assert fragment not in doc_text_lower

    real_key_patterns = (
        r"\bsk-[a-z0-9_-]{20,}\b",
        r"\blive_[a-z0-9]{24,}\b",
        r"\b[A-Za-z0-9_-]{32,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\b",
    )
    for pattern in real_key_patterns:
        assert re.search(pattern, doc_text) is None


def test_api_football_real_smoke_evidence_doc_contains_no_raw_provider_payload() -> None:
    doc_text = _read_phase_25_doc()
    doc_text_lower = doc_text.lower()

    assert "```json" not in doc_text_lower
    assert '{"' not in doc_text
    assert '"response":' not in doc_text_lower
    assert '"parameters":' not in doc_text_lower
    assert '"errors":' not in doc_text_lower
    assert '"results":' not in doc_text_lower
    assert "raw provider payload" in doc_text_lower
    assert "raw provider payloads" in doc_text_lower


def test_api_football_real_smoke_evidence_doc_does_not_claim_activation_or_writes() -> None:
    doc_text = _read_phase_25_doc().lower()

    forbidden_claims = (
        "db_writes=true",
        "prediction_created=true",
        "betting_created=true",
        "db_ingestion_enabled=true",
        "prediction_creation_enabled=true",
        "betting_enabled=true",
        "provider_enabled=true",
        "api_football_connected=true",
        "public_endpoint_enabled=true",
        "network_calls_enabled=true",
        "real api-football calls in automated tests are allowed",
        "phase 25 enables provider activation",
        "phase 25 enables db ingestion",
        "phase 25 enables prediction",
        "phase 25 enables betting",
        "phase 25 adds a public endpoint",
    )
    for claim in forbidden_claims:
        assert claim not in doc_text

    required_forbidden_scope = (
        "making real api-football calls in automated tests",
        "adding db ingestion",
        "db models",
        "alembic migrations",
        "adding prediction",
        "adding odds, bookmaker, stake, betting",
        "adding public endpoints",
        "frontend changes",
        "apps/web/lib/integrations",
        "_references/public-apis",
        "docs/api-catalog.md",
    )
    for fragment in required_forbidden_scope:
        assert fragment in doc_text
