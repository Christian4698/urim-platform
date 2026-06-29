# Phase 9 URIM Provider Sandbox Integration QA

## Objective
Strengthen the Provider Sandbox Adapter QA integration before any real provider onboarding. Phase 9 keeps URIM/Kairos contract- and readiness-only: no API-Football connector, no internet/provider calls, no API keys, no bookmaker, no real betting, no ML, no real prediction, no production seed, no auth/RBAC build-out, no database ingestion, no migration/model change, and no real or fake production sports result.

## Files To Modify Or Create
- `docs/exec-plans/active/009-phase-9-provider-sandbox-integration-qa.md`
- `apps/api/app/core/constants.py`
- `apps/api/app/core/security.py`
- `apps/api/app/main.py`
- `apps/api/app/api/v1/routes/fixtures.py`
- `apps/api/app/api/v1/routes/post_match.py`
- `apps/api/app/api/v1/routes/predictions.py`
- `apps/api/app/api/v1/routes/providers.py`
- `apps/api/app/modules/providers/__init__.py`
- `apps/api/app/modules/providers/contracts.py`
- `apps/api/app/modules/providers/sandbox.py`
- `apps/api/app/schemas/providers.py`
- `apps/api/tests/test_api_foundation.py`
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_provider_contracts.py`
- `apps/api/tests/test_provider_sandbox.py`
- `apps/api/tests/test_security_hardening.py`
- `apps/api/README.md`
- `apps/api/pyproject.toml`
- `docs/21_API_AND_DATABASE_SPEC.md`
- `docs/29_PROVIDER_READINESS_CONTRACTS.md`

## Out Of Scope
- No API-Football connector, real provider adapter, outbound HTTP, scraping, or internet call.
- No API key, credential loading, provider auth flow, bookmaker integration, real betting, stake, payout, or payment flow.
- No ML, calibration engine, real prediction creation, post-match learning activation, or real official result verification.
- No production seed, real sports fixture/result import, fake production sports result, DB ingestion, SQLAlchemy model change, Alembic migration, full auth/RBAC, session, cookie, CORS expansion, docs portal, scheduler, queue, retry execution, or circuit breaker implementation.

## Phase 9 Work
- Update runtime metadata and documentation wording to `phase-9-provider-sandbox-integration-qa`.
- Correct Phase 8 audit notes: avoid shadowed `payload` variables, document `official_result_envelope` as sandbox-only QA helper, and test defensive redaction against test-only sensitive placeholder values.
- Extend provider readiness/status schemas with onboarding, rate-limit/quota, and reconciliation requirements as disabled/readiness-only contract metadata.
- Enrich `GET /api/v1/providers/sandbox/status` with QA/onboarding metadata and the sandbox flow `identity -> payloads -> raw_reference -> observation -> quality_report -> canonical_mapping_placeholder -> official_result_envelope_placeholder`.
- Keep `POST /api/v1/providers/sandbox/status` and other dangerous POST routes unavailable with `405`.

## Expected Tests
- Phase 9 metadata appears consistently in health, readiness, capabilities, provider readiness, sandbox status, and skeleton endpoints.
- Sandbox full flow preserves provenance, timezone-aware timestamps, `observed_at <= available_at <= fetched_at`, stable raw hashes, sanitized payload summaries, no DB ingestion, no prediction creation, and no network sockets.
- Sandbox payloads remain `DEMO_NON_PROD` / `PLACEHOLDER` only and contain no real teams, scores, results, winners, real provider IDs, bookmaker fields, credentials, or leaked fake secrets.
- Readiness/status expose disabled rate-limit/quota contracts, reconciliation readiness, onboarding requirements, all provider capabilities disabled, and no secrets.
- `SportsDataProviderProtocol` remains provider-contract-only; `official_result_envelope` stays sandbox-only.
- Existing Phase 2 temporal, append-only, and database tests remain intact; `alembic check` reports no new migration operations.

## Risks E001-E084
- E001-E005: provenance completeness, missing data clarity, source quality, and temporal availability guardrails.
- E026: no advice or prediction creation introduced.
- E049: pre-match/live separation remains intact; live stays disabled.
- E065-E074: provider fallback, timestamp discipline, immutability readiness, versioning, outlier/missing handling, mapping readiness, latency/rate-limit readiness, and API key protection.
- E079: no retroactive result mutation path added.
- E083: no real betting or loss-recovery behavior introduced.
- E084: sandbox/readiness limits and onboarding gaps are explicit.

## Validation Strategy
Run from `apps/api`:
- `pip install -e ".[dev]"`
- `ruff check .`
- `pytest`
- `git diff --check`
- `DATABASE_URL=postgresql+psycopg://urim:urim_local_only@localhost:5432/urim_local alembic check`

Docker/PostgreSQL may be started only if needed for `alembic check`; apply existing migrations only and do not delete Docker volumes with `-v`.

## Implementation Result
Status: implemented and validated locally.

Phase 8 audit notes corrected:
- Shadowing `payload` variables in sandbox golden payload tests were renamed to `golden_payload`.
- `official_result_envelope` is documented and tested as a sandbox-only QA helper, not part of `SportsDataProviderProtocol`.
- Test-only sensitive placeholder payloads verify recursive redaction without exposing fake secret values.

Provider sandbox integration QA additions:
- Runtime metadata now reports `phase-9-provider-sandbox-integration-qa`.
- Provider readiness and sandbox status expose onboarding, rate-limit/quota, and reconciliation readiness requirements.
- Sandbox status exposes the QA flow `identity -> payloads -> raw_reference -> observation -> quality_report -> canonical_mapping_placeholder -> official_result_envelope_placeholder`.
- Sandbox safeguards explicitly keep network calls, credentials, DB ingestion, prediction creation, official result verification, and Post-Match Learning disabled.

Documentation updated:
- `docs/21_API_AND_DATABASE_SPEC.md` documents Phase 9 sandbox integration QA.
- `docs/29_PROVIDER_READINESS_CONTRACTS.md` documents sandbox-only official result envelopes, onboarding prerequisites, rate-limit/quota readiness, and reconciliation readiness.

Validation results:
- `pip install -e ".[dev]"`: passed.
- `ruff check .`: passed.
- `pytest`: passed with 91 passed, 2 skipped, 1 known Starlette/TestClient warning.
- `git diff --check`: passed before this result update.
- Initial `alembic check` without Docker-ready Postgres hung on local DB connection and was stopped.
- `docker compose -f infra/docker/docker-compose.yml up -d`: passed.
- `alembic upgrade head`: passed using existing migrations only.
- `alembic check`: passed; no new upgrade operations detected.
- `docker compose -f infra/docker/docker-compose.yml stop`: passed; volumes preserved.

Guardrail result:
- No Alembic migration or SQLAlchemy model changes.
- No provider HTTP client usage in application code.
- No API-Football connector, bookmaker, real betting, ML, real prediction, production seed, DB ingestion, or production sports result added.
- Bet Center remains virtual/internal.
- Phase 2 temporal, append-only, immutable prediction, and anti-look-ahead protections remain intact.

Remaining risks:
- Phase 9 remains QA/readiness-only; real provider onboarding still requires license review, quota/rate-limit proof, latency measurement, anonymized real golden payloads, monitoring, reconciliation, and independent security audit.
- Complete auth/RBAC remains out of scope.
- Starlette/TestClient emits a dependency warning from the installed stack.
