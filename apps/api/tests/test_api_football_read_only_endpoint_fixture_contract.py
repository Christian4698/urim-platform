from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "45_API_FOOTBALL_READ_ONLY_ENDPOINT_SELECTION_AND_FIXTURE_CONTRACT.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"

ALLOWED_FIXTURE_FIELDS = (
    "provider",
    "provider_fixture_id",
    "provider_league_id",
    "provider_season",
    "fixture_date",
    "fixture_timezone",
    "fixture_status_short",
    "fixture_status_long",
    "home_team_provider_id",
    "home_team_name",
    "away_team_provider_id",
    "away_team_name",
    "goals_home",
    "goals_away",
    "score_halftime_home",
    "score_halftime_away",
    "score_fulltime_home",
    "score_fulltime_away",
    "payload_hash",
    "payload_top_level_keys",
)


def _literal(*parts: str) -> str:
    return "".join(parts)


def _read_phase_26_doc() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _allowed_field_lines(doc_text: str) -> list[str]:
    in_fields = False
    fields: list[str] = []

    for line in doc_text.splitlines():
        if line == "## Allowed read-only fields":
            in_fields = True
            continue
        if in_fields and line.startswith("## "):
            break
        match = re.fullmatch(r"- `([a-z_]+)`", line)
        if in_fields and match:
            fields.append(match.group(1))

    return fields


def test_api_football_read_only_endpoint_fixture_contract_doc_exists() -> None:
    doc_text = _read_phase_26_doc()

    assert "Phase 26" in doc_text
    assert "status=documentation_only_read_only_endpoint_selection" in doc_text


def test_api_football_read_only_endpoint_fixture_contract_prioritizes_fixtures() -> None:
    doc_text = _read_phase_26_doc()

    assert "`/fixtures`: priority endpoint" in doc_text
    assert "## Why /fixtures is priority" in doc_text
    assert "without requiring odds or provider predictions" in doc_text


def test_api_football_read_only_endpoint_fixture_contract_documents_useful_read_only_endpoints() -> None:
    doc_text = _read_phase_26_doc()

    for endpoint in ("/leagues", "/teams", "/standings"):
        assert endpoint in doc_text
    assert "Allowed now for documentation and contract planning only" in doc_text


def test_api_football_read_only_endpoint_fixture_contract_forbids_predictions_and_odds() -> None:
    doc_text = _read_phase_26_doc()

    assert "`/predictions`: forbidden" in doc_text
    assert "`/odds`: forbidden" in doc_text
    assert "## No betting/odds yet" in doc_text
    assert "## No prediction yet" in doc_text


def test_api_football_read_only_endpoint_fixture_contract_documents_no_scope_claims() -> None:
    doc_text = _read_phase_26_doc()

    assert "## No DB ingestion yet" in doc_text
    assert "No DB ingestion is enabled" in doc_text
    assert "No prediction is created" in doc_text
    assert "No betting, odds, bookmaker or stake path is enabled" in doc_text


def test_api_football_read_only_endpoint_fixture_contract_lists_only_safe_fixture_fields() -> None:
    doc_text = _read_phase_26_doc()
    normalized_doc_text = " ".join(doc_text.split())

    assert tuple(_allowed_field_lines(doc_text)) == ALLOWED_FIXTURE_FIELDS
    for field in ALLOWED_FIXTURE_FIELDS:
        assert field in doc_text
    assert "not a provider observation storage contract yet" in doc_text
    assert "Later ingestion must add full provenance and temporal fields before any DB write" in normalized_doc_text


def test_api_football_read_only_endpoint_fixture_contract_index_references_phase_26_doc() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "45_API_FOOTBALL_READ_ONLY_ENDPOINT_SELECTION_AND_FIXTURE_CONTRACT.md" in index_text


def test_api_football_read_only_endpoint_fixture_contract_has_no_secret_or_provider_url_material() -> None:
    doc_text = _read_phase_26_doc()
    doc_text_lower = doc_text.lower()

    forbidden_fragments = (
        _literal("http", "://"),
        _literal("https", "://"),
        _literal("api-football", ".com"),
        _literal("api", "-sports"),
        _literal("rapid", "api"),
        _literal("x", "-rapid", "api"),
        _literal("x", "-apisports-key"),
        _literal("x", "-api-key"),
        _literal("authorization", ":"),
        _literal("bearer", " "),
        _literal("api_key", "="),
        _literal("api", "key"),
        _literal("api-key", ":"),
        _literal("credential", "="),
        _literal("token", "="),
        _literal("secret", "="),
        _literal("provider", "_credentials"),
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


def test_api_football_read_only_endpoint_fixture_contract_contains_no_raw_provider_payload() -> None:
    doc_text = _read_phase_26_doc()
    doc_text_lower = doc_text.lower()

    assert _literal("```", "json") not in doc_text_lower
    assert _literal("{", '"') not in doc_text
    assert _literal('"', "fixture", '":') not in doc_text_lower
    assert _literal('"', "response", '":') not in doc_text_lower
    assert _literal('"', "parameters", '":') not in doc_text_lower
    assert "provider response bodies" in doc_text_lower


def test_api_football_read_only_endpoint_fixture_contract_does_not_claim_activation() -> None:
    doc_text = _read_phase_26_doc().lower()

    forbidden_claims = (
        _literal("db_ingestion_enabled", "=true"),
        _literal("prediction_created", "=true"),
        _literal("prediction_creation_enabled", "=true"),
        _literal("betting_created", "=true"),
        _literal("betting_enabled", "=true"),
        _literal("provider_enabled", "=true"),
        _literal("api_football_connected", "=true"),
        _literal("public_endpoint_enabled", "=true"),
        _literal("network_calls_enabled", "=true"),
        "phase 26 enables db ingestion",
        "phase 26 enables prediction",
        "phase 26 enables betting",
        "phase 26 adds a public endpoint",
        "real api-football calls in automated tests are allowed",
    )
    for claim in forbidden_claims:
        assert claim not in doc_text
