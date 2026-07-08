from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = (
    REPO_ROOT / "apps" / "api" / "scripts" / "run_fixture_first_real_local_smoke.ps1"
)
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "52_API_FOOTBALL_FIXTURE_COMPACT_SMOKE_RUNNER.md"
)
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
COMPLETED_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "033-phase-33-api-football-fixture-compact-smoke-runner.md"
)


def _runner_source() -> str:
    return RUNNER_PATH.read_text(encoding="utf-8")


def _write_host_lines(source: str) -> list[str]:
    return [line.strip() for line in source.splitlines() if "Write-Host" in line]


def test_fixture_compact_smoke_runner_exists_and_references_compact_script() -> None:
    source = _runner_source()

    assert RUNNER_PATH.exists()
    assert RUNNER_PATH.is_file()
    assert "api_football_fixture_first_real_local_smoke.py" in source
    assert "python .\\scripts\\api_football_fixture_first_real_local_smoke.py" in source


def test_fixture_compact_smoke_runner_sets_required_local_env_gates() -> None:
    source = _runner_source()

    expected_assignments = {
        "$env:APP_ENV": '"development"',
        "$env:URIM_API_FOOTBALL_FIXTURE_SMOKE_ENABLED": '"1"',
        "$env:URIM_API_FOOTBALL_FIXTURE_SMOKE_AUTH": "$authMaterial",
        "$env:URIM_API_FOOTBALL_FIXTURE_SMOKE_BASE_URL": "$providerReference",
        "$env:URIM_API_FOOTBALL_FIXTURE_SMOKE_DATE": "$smokeDateValue",
        "$env:URIM_API_FOOTBALL_FIXTURE_SMOKE_TIMEZONE": '"Africa/Kinshasa"',
        "$env:URIM_API_FOOTBALL_FIXTURE_SMOKE_READ_ONLY": '"1"',
        "$env:URIM_API_FOOTBALL_FIXTURE_SMOKE_NON_PROD": '"1"',
        "$env:URIM_LOCAL_PREFLIGHT_NO_DB_WRITE_CONFIRMED": '"1"',
        "$env:URIM_LOCAL_PREFLIGHT_NO_PREDICTION_CONFIRMED": '"1"',
        "$env:URIM_LOCAL_PREFLIGHT_NO_BETTING_CONFIRMED": '"1"',
    }
    for env_name, expected_value in expected_assignments.items():
        assert f"{env_name} = {expected_value}" in source

    assert '[string] $SmokeDate = "2026-07-07"' in source
    assert "Get-ValidatedSmokeDate" in source
    assert "TryParseExact" in source
    assert '"https://v3.football.api-sports.io/fixtures"' in source


def test_fixture_compact_smoke_runner_reads_local_auth_without_printing_it() -> None:
    source = _runner_source()
    output_lines = "\n".join(_write_host_lines(source))

    assert "Get-Clipboard" in source
    assert 'Read-Host "Enter local API-Football auth material" -AsSecureString' in source
    assert "$authMaterial" not in output_lines
    assert "$clipboardText" not in output_lines
    assert "URIM_API_FOOTBALL_FIXTURE_SMOKE_AUTH" not in output_lines


def test_fixture_compact_smoke_runner_cleans_sensitive_env_and_clipboard() -> None:
    source = _runner_source()

    assert "finally {" in source
    assert 'if ($envName -eq "URIM_API_FOOTBALL_FIXTURE_SMOKE_AUTH")' in source
    assert 'Remove-Item -LiteralPath "Env:$envName"' in source
    assert 'Set-Clipboard -Value ""' in source
    assert "$authMaterial = $null" in source
    assert "$authSecure = $null" in source
    assert "$clipboardText = $null" in source
    assert "$providerReference = $null" in source


def test_fixture_compact_smoke_runner_does_not_log_provider_url_or_content() -> None:
    source = _runner_source()
    output_lines = "\n".join(_write_host_lines(source)).lower()

    assert "https://v3.football.api-sports.io/fixtures" not in output_lines
    assert "$providerreference" not in output_lines
    assert "raw_payload" not in source.lower()
    assert "smoke_payload" not in source.lower()
    assert "payload" not in source.lower()
    assert '"response"' not in source.lower()


def test_fixture_compact_smoke_runner_has_no_embedded_auth_value() -> None:
    source = _runner_source()
    source_lower = source.lower()
    auth_assignment = re.search(
        r"\$env:URIM_API_FOOTBALL_FIXTURE_SMOKE_AUTH\s*=\s*(.+)",
        source,
    )

    assert auth_assignment is not None
    assert auth_assignment.group(1).strip() == "$authMaterial"
    forbidden_fragments = (
        "authorization",
        "bearer ",
        "x-rapidapi",
        "rapidapi",
        "api_key=",
        "apikey",
        "api-key=",
        "secret=",
        "token=",
        "demo_non_prod",
        "local_only_fake",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source_lower


def test_fixture_compact_smoke_runner_has_no_active_prediction_or_betting_scope() -> None:
    source_lower = _runner_source().lower()
    allowed_negative_fragments = (
        "urim_local_preflight_no_prediction_confirmed",
        "urim_local_preflight_no_betting_confirmed",
    )
    active_scope_source = source_lower
    for fragment in allowed_negative_fragments:
        active_scope_source = active_scope_source.replace(fragment, "")

    for fragment in ("odds", "bookmaker", "stake", "betting", "prediction"):
        assert fragment not in active_scope_source


def test_fixture_compact_smoke_runner_does_not_write_env_files_or_commit() -> None:
    source_lower = _runner_source().lower()
    forbidden_fragments = (
        ".env",
        ".env.example",
        "set-content",
        "add-content",
        "out-file",
        "export-clixml",
        "new-item",
        "start-transcript",
        "git commit",
        "git ",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source_lower


def test_fixture_compact_smoke_runner_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_text_lower = doc_text.lower()

    assert "Phase 33" in doc_text
    assert "compact output only" in doc_text_lower
    assert "## No DB write" in doc_text
    assert "## No prediction" in doc_text
    assert "## No betting/odds" in doc_text
    assert "no automated tests may call the real provider" in doc_text_lower


def test_fixture_compact_smoke_runner_doc_and_completed_plan_are_indexed() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert DOC_PATH.exists()
    assert COMPLETED_PLAN_PATH.exists()
    assert "52_API_FOOTBALL_FIXTURE_COMPACT_SMOKE_RUNNER.md" in index_text
