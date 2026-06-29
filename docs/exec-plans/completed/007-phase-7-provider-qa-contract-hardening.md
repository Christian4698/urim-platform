# Phase 7 URIM Provider QA Contract Hardening

## Objective
Harden provider QA contracts before any real provider integration. Phase 7 corrects minor Phase 6 audit findings, adds payload redaction and non-production golden payload checks, and keeps providers disabled.

## Files To Modify Or Create
- `docs/exec-plans/active/007-phase-7-provider-qa-contract-hardening.md`
- `apps/api/app/core/constants.py`
- `apps/api/app/core/security.py`
- `apps/api/app/main.py`
- `apps/api/app/modules/providers/quality.py`
- `apps/api/app/schemas/providers.py`
- `apps/api/tests/test_api_foundation.py`
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_provider_contracts.py`
- `apps/api/tests/test_security_hardening.py`
- `apps/api/tests/fixtures/provider_golden_payloads.py`
- `apps/api/README.md`
- `apps/api/pyproject.toml`
- `docs/21_API_AND_DATABASE_SPEC.md`
- `docs/29_PROVIDER_READINESS_CONTRACTS.md`

## Out Of Scope
- No API-Football connector, provider adapter, outbound HTTP, scraping, or internet call.
- No API key, credential field, secret loading, or provider auth flow.
- No bookmaker integration, real betting, real stake, payout, or payment flow.
- No ML, calibration engine, real prediction creation, or post-match learning engine.
- No production seed, real sports fixture/result import, or fake production sports result.
- No full auth/RBAC, sessions, cookies, CORS expansion, docs portal, or deployment change.
- No migration edits and no SQLAlchemy model edits.

## Provider QA Work
- Update API phase metadata to `phase-7-provider-qa-contract-hardening`.
- Replace legacy `phase_N_security_assertions` aliases with `phase_seven_security_assertions`.
- Add direct validation for `assert_no_production_mock_fallback`.
- Add explicit `is_temporal_order_valid` calculation and use it in `build_quality_report`.
- Add `assert_network_calls_disabled`.
- Add recursive `sanitize_provider_payload` masking sensitive keys containing `api_key`, `token`, `authorization`, `secret`, `password`, `bearer`, `credential`, or `provider_credentials`.
- Extend provider readiness with exact QA requirements: `license_review_required`, `quota_and_rate_limit_required`, `golden_payloads_required`, `payload_redaction_required`, `monitoring_required`, `independent_audit_required`, `no_production_mock_fallback`.
- Add test-only golden payloads marked `DEMO_NON_PROD` / `PLACEHOLDER`; no real teams, fixtures, scores, or results.

## Expected Tests
- Redaction masks sensitive nested payload keys and preserves safe fields.
- Test-only golden payloads are explicitly non-production and contain no real sports results.
- Mock fallback and network-enabled flags are rejected.
- Quality report computes temporal validity explicitly.
- Provider readiness stays read-only, provider-disabled, secret-free, and socket-free.
- `POST /api/v1/providers/readiness` returns `405`.
- Existing Phase 2 temporal, append-only, and database tests remain intact.
- `alembic check` detects no new migration operations.

## Risks E001-E084
- E001-E005: provenance completeness, missing handling, and temporal availability guardrails.
- E026: no advice or prediction creation introduced.
- E049: pre-match/live separation remains intact; live stays disabled.
- E065-E074: provider fallback, immutability readiness, versioning, missing-data clarity, mapping, latency readiness, and API key protection.
- E079: no retroactive result mutation path added.
- E083: no real betting or loss-recovery behavior introduced.
- E084: readiness limitations and QA requirements are explicit.

## Validation Strategy
Run from `apps/api`:
- `pip install -e ".[dev]"`
- `ruff check .`
- `pytest`
- `git diff --check`
- `DATABASE_URL=postgresql+psycopg://urim:urim_local_only@localhost:5432/urim_local alembic check`

Docker/PostgreSQL may be started only if needed for `alembic check`; do not delete Docker volumes with `-v`.

## Implementation Result
Status: implemented and validated locally.

Phase 6 audit items corrected:
- Added direct tests for `assert_no_production_mock_fallback`.
- `build_quality_report` now computes `temporal_order_valid` through explicit temporal ordering logic.
- Legacy `phase_N_security_assertions` aliases were removed; only `phase_seven_security_assertions` remains.

Provider QA additions:
- Recursive payload redaction masks sensitive keys.
- Network-enabled and production mock fallback checks reject bypassed provider identities.
- Readiness exposes exact QA requirements for license review, quotas/rate limits, golden payloads, redaction, monitoring, independent audit, and no production mock fallback.
- Test-only golden payloads are marked `DEMO_NON_PROD` / `PLACEHOLDER` and contain no real sports result.

Validation results:
- `pip install -e ".[dev]"`: passed.
- `ruff check .`: passed.
- `pytest` without `DATABASE_URL`: 78 passed, 2 skipped, 1 warning.
- `git diff --check`: passed.
- `docker compose -f infra/docker/docker-compose.yml up -d`: passed.
- `alembic upgrade head`: passed against local Postgres.
- `alembic check`: passed; no new upgrade operations detected.
- `pytest` with local `DATABASE_URL`: 80 passed, 1 warning.
- `docker compose -f infra/docker/docker-compose.yml stop`: passed; volumes preserved.

Guardrail result:
- No Alembic or SQLAlchemy DB model changes.
- No provider HTTP client usage in application code.
- No API-Football connector, bookmaker, real betting, ML, real prediction, or production seed added.
- Bet Center remains virtual/internal.
- Phase 2 temporal and append-only protections remain intact.

Remaining risks:
- Phase 7 remains contract/QA-only; real provider onboarding still needs license, quota, latency, payload, reconciliation, redaction, monitoring, and audit validation in a future phase.
- No complete auth/RBAC is added in Phase 7.
- Starlette/TestClient emits a dependency warning from the installed stack.
