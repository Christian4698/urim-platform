from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "53_FIXTURE_INGESTION_READINESS_PLAN.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "active"
    / "034-phase-34-fixture-ingestion-readiness-plan.md"
)
COMPLETED_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "034-phase-34-fixture-ingestion-readiness-plan.md"
)


def _doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_fixture_ingestion_readiness_doc_exists() -> None:
    assert DOC_PATH.exists()
    assert DOC_PATH.is_file()


def test_fixture_ingestion_readiness_doc_states_negative_scope() -> None:
    doc_text = _doc_text()
    doc_lower = doc_text.lower()

    required_phrases = (
        "no db write",
        "no alembic migration",
        "no sqlalchemy model",
        "no public endpoint",
        "no frontend",
        "no real api call",
        "no prediction",
        "no betting/odds",
    )
    for phrase in required_phrases:
        assert phrase in doc_lower


def test_fixture_ingestion_readiness_doc_contains_candidate_fields() -> None:
    doc_text = _doc_text()

    required_fields = (
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
        "fetched_at",
        "source_mode",
    )
    for field in required_fields:
        assert f"`{field}`" in doc_text


def test_fixture_ingestion_readiness_doc_contains_required_strategies() -> None:
    doc_lower = _doc_text().lower()

    required_topics = (
        "idempotence",
        "deduplication",
        "payload_hash",
        "provider_fixture_id",
        "audit trail",
        "freshness",
        "no raw payload by default",
        "rollback",
        "quota",
        "live",
        "incomplete",
        "postponed",
        "cancelled",
        "future phase 35",
    )
    for topic in required_topics:
        assert topic in doc_lower


def test_fixture_ingestion_readiness_doc_has_future_phase_35_criteria() -> None:
    doc_lower = _doc_text().lower()

    assert "future phase 35 authorization criteria" in doc_lower
    required_criteria = (
        "staging schema proposal",
        "idempotence and deduplication tests",
        "rollback and quarantine procedure",
        "quota, rate-limit, retry, and monitoring plan",
        "security review",
        "temporal review",
        "staging-only",
    )
    for criterion in required_criteria:
        assert criterion in doc_lower


def test_fixture_ingestion_readiness_doc_has_no_provider_secret_or_raw_content() -> None:
    doc_lower = _doc_text().lower()

    forbidden_fragments = (
        "x-apisports-key",
        "x-rapidapi",
        "authorization:",
        "bearer ",
        "api_key=",
        "apikey",
        "api-key=",
        "secret=",
        "token=",
        "```json",
        '"response"',
        '"fixture"',
        '"league"',
        '"teams"',
        "normalized_count=108",
        "108 fixtures",
        "dayton dutch lions",
        "kings hammer columbus",
        "fc copenhagen",
    )
    for fragment in forbidden_fragments:
        assert fragment not in doc_lower


def test_fixture_ingestion_readiness_doc_is_indexed_and_plan_completed() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "53_FIXTURE_INGESTION_READINESS_PLAN.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
